import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import User, UserProfile
from apps.catalog.models import Category, Product
from apps.inventory.models import StockBalance

ROLE_MAP = {
    "admin": UserProfile.Role.ADMIN,
    "approver": UserProfile.Role.APPROVER,
    "operations": UserProfile.Role.OPERATOR,
    "operator": UserProfile.Role.OPERATOR,
    "requester": UserProfile.Role.REQUESTER,
    "industry": UserProfile.Role.INDUSTRY
    if hasattr(UserProfile.Role, "INDUSTRY")
    else UserProfile.Role.REQUESTER,
}


class Command(BaseCommand):
    help = "Valida e importa um pacote legado exportado sem alterar o sistema de origem."

    def add_arguments(self, parser):
        parser.add_argument("input", type=Path, help="Arquivo JSON exportado do sistema antigo.")
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Confirma a gravação. Sem esta opção, executa somente a validação.",
        )

    def handle(self, *args, **options):
        input_path = options["input"]
        if not input_path.exists():
            raise CommandError(f"Arquivo não encontrado: {input_path}")
        try:
            payload = json.loads(input_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f"Não foi possível ler o pacote: {exc}") from exc

        errors = self.validate_payload(payload)
        if errors:
            raise CommandError("Pacote inválido:\n- " + "\n- ".join(errors))

        counts = {
            key: len(payload.get(key, [])) for key in ("users", "categories", "items", "stock")
        }
        mode = "APLICAÇÃO" if options["apply"] else "SIMULAÇÃO"
        self.stdout.write(self.style.SUCCESS(f"{mode} validada: {counts}"))
        if options["apply"]:
            with transaction.atomic():
                self.apply_payload(payload)
            self.stdout.write(self.style.SUCCESS("Importação concluída com transação confirmada."))
        else:
            self.stdout.write("Nenhuma alteração foi feita. Use --apply para confirmar.")

    @staticmethod
    def validate_payload(payload):
        errors = []
        required = {"source_version", "users", "categories", "items", "stock"}
        if not isinstance(payload, dict):
            return ["A raiz do pacote deve ser um objeto JSON."]
        errors.extend(f"Campo obrigatório ausente: {key}" for key in required - payload.keys())
        for key in ("users", "categories", "items", "stock"):
            if key not in payload:
                continue
            if not isinstance(payload[key], list):
                errors.append(f"{key} deve ser uma lista.")
        rows = {
            key: payload.get(key, []) if isinstance(payload.get(key, []), list) else []
            for key in ("users", "categories", "items", "stock")
        }
        if not str(payload.get("source_version", "")).strip():
            errors.append("source_version não pode estar vazio.")

        emails = set()
        for index, user in enumerate(rows["users"]):
            if not isinstance(user, dict):
                errors.append(f"users[{index}] deve ser um objeto.")
                continue
            email = str(user.get("email", "")).strip().lower()
            if not email or "@" not in email:
                errors.append(f"users[{index}].email inválido ou ausente.")
            if email in emails:
                errors.append(f"E-mail duplicado: {email}")
            emails.add(email)
            if user.get("role") not in ROLE_MAP:
                errors.append(f"Perfil legado inválido em users[{index}]: {user.get('role')}")

        category_names = set()
        for index, category in enumerate(rows["categories"]):
            if not isinstance(category, dict):
                errors.append(f"categories[{index}] deve ser um objeto.")
                continue
            name = str(category.get("name", "")).strip()
            if not name:
                errors.append(f"categories[{index}].name é obrigatório.")
            if name.casefold() in category_names:
                errors.append(f"Categoria duplicada: {name}")
            category_names.add(name.casefold())

        codes = set()
        for index, item in enumerate(rows["items"]):
            if not isinstance(item, dict):
                errors.append(f"items[{index}] deve ser um objeto.")
                continue
            code = str(item.get("code", "")).strip()
            if not code or not str(item.get("name", "")).strip():
                errors.append(f"items[{index}] exige code e name.")
            if code.casefold() in codes:
                errors.append(f"Código duplicado: {code}")
            codes.add(code.casefold())
            category = str(item.get("category", "")).strip()
            if category and category.casefold() not in category_names:
                errors.append(f"Categoria inexistente em items[{index}]: {category}")
            try:
                minimum = item.get("min_stock", 0)
                if isinstance(minimum, bool) or int(minimum) < 0:
                    raise ValueError
            except (TypeError, ValueError):
                errors.append(f"Estoque mínimo inválido em items[{index}].")

        stock_codes = set()
        for index, stock in enumerate(rows["stock"]):
            if not isinstance(stock, dict):
                errors.append(f"stock[{index}] deve ser um objeto.")
                continue
            code = str(stock.get("code", "")).strip()
            if code.casefold() not in codes:
                errors.append(f"stock[{index}].code não possui item correspondente.")
            if code.casefold() in stock_codes:
                errors.append(f"Saldo duplicado para o item {code}.")
            stock_codes.add(code.casefold())
            try:
                on_hand = stock.get("qty_on_hand", 0)
                reserved = stock.get("qty_reserved", 0)
                if (
                    isinstance(on_hand, bool)
                    or isinstance(reserved, bool)
                    or int(on_hand) != float(on_hand)
                    or int(reserved) != float(reserved)
                    or int(on_hand) < 0
                    or int(reserved) < 0
                    or int(reserved) > int(on_hand)
                ):
                    raise ValueError
            except (TypeError, ValueError, OverflowError):
                errors.append(f"Quantidade/saldo inválido em stock[{index}].")
        return errors

    @staticmethod
    def apply_payload(payload):
        categories = {
            row["name"].strip().casefold(): Category.objects.get_or_create(
                name=row["name"].strip()
            )[0]
            for row in payload["categories"]
        }
        products = {}
        for row in payload["items"]:
            category = categories.get(str(row.get("category", "")).strip().casefold())
            product, _ = Product.objects.update_or_create(
                sku=str(row["code"]).strip(),
                defaults={
                    "name": row["name"].strip(),
                    "description": row.get("description", ""),
                    "category": category,
                    "unit": row.get("unit", "unidade"),
                    "minimum_stock": int(row.get("min_stock", 0)),
                    "is_active": row.get("status", "ativo") == "ativo",
                },
            )
            products[product.sku.casefold()] = product
        for row in payload["users"]:
            email = row["email"].strip().lower()
            first_name, _, last_name = row.get("name", "").partition(" ")
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "username": email.split("@", 1)[0],
                    "first_name": first_name,
                    "last_name": last_name,
                },
            )
            if created:
                user.set_unusable_password()
            user.is_active = bool(row.get("active", True))
            user.first_name, user.last_name = first_name, last_name
            user.save(update_fields=["is_active", "first_name", "last_name", "password"])
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = ROLE_MAP[row["role"]]
            profile.department = row.get("department", "")
            profile.save(update_fields=["role", "department", "updated_at"])
        for row in payload["stock"]:
            product = products[str(row["code"]).strip().casefold()]
            StockBalance.objects.update_or_create(
                product=product,
                defaults={
                    "quantity": int(row.get("qty_on_hand", 0)),
                    "reserved_quantity": int(row.get("qty_reserved", 0)),
                },
            )
