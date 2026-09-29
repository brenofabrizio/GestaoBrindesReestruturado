import json
import secrets
import string
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import User, UserProfile


DEFAULT_ACCOUNTS = [
    {
        "email": "admin@gestaobrindes.com",
        "first_name": "Administrador",
        "last_name": "Gestão Brindes",
        "role": UserProfile.Role.ADMIN,
        "department": "Administração",
    },
    {
        "email": "aprovador@gestaobrindes.com",
        "first_name": "Aprovador",
        "last_name": "Gestão Brindes",
        "role": UserProfile.Role.APPROVER,
        "department": "Administração",
    },
    {
        "email": "operador@gestaobrindes.com",
        "first_name": "Operador",
        "last_name": "Estoque",
        "role": UserProfile.Role.OPERATOR,
        "department": "Operações",
    },
    {
        "email": "solicitante@gestaobrindes.com",
        "first_name": "Solicitante",
        "last_name": "Demonstração",
        "role": UserProfile.Role.REQUESTER,
        "department": "Comercial",
    },
    {
        "email": "industria@gestaobrindes.com",
        "first_name": "Indústria",
        "last_name": "Demonstração",
        "role": UserProfile.Role.INDUSTRY,
        "department": "Indústria",
    },
]


class Command(BaseCommand):
    help = "Cria ou atualiza as contas iniciais sem versionar senhas."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=Path,
            help="JSON local com contas. Sem este argumento, usa os cinco perfis padrão.",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Grava as contas. Sem esta opção, apenas valida e simula.",
        )
        parser.add_argument(
            "--reset-passwords",
            action="store_true",
            help="Gera novas senhas também para contas que já existem.",
        )
        parser.add_argument(
            "--show-passwords",
            action="store_true",
            help="Exibe senhas geradas no terminal. Use apenas em sessão segura.",
        )
        parser.add_argument(
            "--credentials-file",
            type=Path,
            help="Salva as credenciais geradas em arquivo local fora do Git.",
        )

    def handle(self, *args, **options):
        accounts = self.load_accounts(options.get("file"))
        self.validate_accounts(accounts)

        if not options["apply"]:
            self.stdout.write(self.style.WARNING("SIMULAÇÃO: nenhuma conta foi alterada."))
            for account in accounts:
                self.stdout.write(f"- {account['email']} ({account['role']})")
            self.stdout.write("Use --apply para confirmar a criação.")
            return

        credentials = []
        with transaction.atomic():
            for account in accounts:
                user, created = User.objects.get_or_create(
                    email=account["email"],
                    defaults={
                        "username": account["email"].split("@", 1)[0],
                        "first_name": account["first_name"],
                        "last_name": account["last_name"],
                    },
                )
                if created or options["reset_passwords"]:
                    password = self.generate_password()
                    user.set_password(password)
                else:
                    password = None

                user.is_active = True
                user.is_staff = account["role"] == UserProfile.Role.ADMIN
                user.is_superuser = account["role"] == UserProfile.Role.ADMIN
                user.first_name = account["first_name"]
                user.last_name = account["last_name"]
                user.save(
                    update_fields=[
                        "is_active",
                        "is_staff",
                        "is_superuser",
                        "first_name",
                        "last_name",
                        "password",
                    ]
                )

                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile.role = account["role"]
                profile.department = account["department"]
                profile.phone = account.get("phone", "")
                profile.save(update_fields=["role", "department", "phone", "updated_at"])

                credentials.append(
                    {
                        "email": account["email"],
                        "role": account["role"],
                        "department": account["department"],
                        "password": password,
                        "password_changed": password is not None,
                    }
                )

        self.stdout.write(self.style.SUCCESS("Contas provisionadas com sucesso."))
        self.write_credentials(credentials, options)

    @staticmethod
    def load_accounts(path):
        if path is None:
            return [dict(account) for account in DEFAULT_ACCOUNTS]
        if not path.exists():
            raise CommandError(f"Arquivo de contas não encontrado: {path}")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f"Não foi possível ler o arquivo de contas: {exc}") from exc
        if isinstance(payload, dict):
            payload = payload.get("accounts")
        if not isinstance(payload, list):
            raise CommandError("O arquivo deve conter uma lista ou um objeto com 'accounts'.")
        return payload

    @staticmethod
    def validate_accounts(accounts):
        required = {"email", "first_name", "last_name", "role", "department"}
        valid_roles = {choice for choice, _ in UserProfile.Role.choices}
        emails = set()
        errors = []
        for index, account in enumerate(accounts):
            missing = required - account.keys()
            if missing:
                errors.append(f"accounts[{index}] sem campos: {', '.join(sorted(missing))}")
            email = str(account.get("email", "")).strip().lower()
            if not email or "@" not in email:
                errors.append(f"accounts[{index}].email inválido")
            if email in emails:
                errors.append(f"E-mail duplicado: {email}")
            emails.add(email)
            if account.get("role") not in valid_roles:
                errors.append(f"Perfil inválido em accounts[{index}]: {account.get('role')}")
        if errors:
            raise CommandError("Arquivo de contas inválido:\n- " + "\n- ".join(errors))

    @staticmethod
    def generate_password():
        alphabet = string.ascii_letters + string.digits + "!@#$%*-_"
        while True:
            password = "".join(secrets.choice(alphabet) for _ in range(24))
            if (
                any(character.islower() for character in password)
                and any(character.isupper() for character in password)
                and any(character.isdigit() for character in password)
                and any(character in "!@#$%*-_" for character in password)
            ):
                return password

    def write_credentials(self, credentials, options):
        visible = options["show_passwords"]
        path = options.get("credentials_file")
        if path:
            path.write_text(json.dumps(credentials, ensure_ascii=False, indent=2), encoding="utf-8")
            self.stdout.write(self.style.WARNING(f"Credenciais salvas somente em: {path}"))
        if visible:
            self.stdout.write("Credenciais geradas (guarde em local seguro):")
            for credential in credentials:
                password = credential["password"] or "(senha preservada; use a senha existente)"
                self.stdout.write(f"- {credential['email']}: {password}")
        elif any(credential["password"] for credential in credentials):
            self.stdout.write(
                "Senhas foram geradas. Use --show-passwords ou --credentials-file para recuperá-las "
                "nesta execução."
            )
