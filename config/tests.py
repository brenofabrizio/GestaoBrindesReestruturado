from django.test import SimpleTestCase

from config.settings import validate_production_environment


class ProductionEnvironmentTests(SimpleTestCase):
    def test_valid_persistent_production_configuration_passes(self):
        env = {
            "DJANGO_DEBUG": "0",
            "DJANGO_SECRET_KEY": "x" * 64,
            "DATABASE_URL": "postgresql://app:secret@db.example.test/app?sslmode=require",
            "DJANGO_ALLOWED_HOSTS": "api.example.test",
            "CORS_ALLOWED_ORIGINS": "https://app.example.test",
            "CSRF_TRUSTED_ORIGINS": "https://api.example.test",
        }

        self.assertEqual(validate_production_environment(env), [])

    def test_production_rejects_non_https_origins(self):
        env = {
            "DJANGO_DEBUG": "0",
            "DJANGO_SECRET_KEY": "x" * 64,
            "DATABASE_URL": "postgresql://app:password@db.example.test/app",
            "DJANGO_ALLOWED_HOSTS": "api.example.test",
            "CORS_ALLOWED_ORIGINS": "http://app.example.test",
            "CSRF_TRUSTED_ORIGINS": "http://api.example.test",
        }

        errors = validate_production_environment(env)

        self.assertTrue(any("CORS_ALLOWED_ORIGINS" in error for error in errors))
        self.assertTrue(any("CSRF_TRUSTED_ORIGINS" in error for error in errors))

    def test_postgres_host_mode_requires_explicit_production_credentials(self):
        env = {
            "DJANGO_DEBUG": "0",
            "DJANGO_SECRET_KEY": "x" * 64,
            "POSTGRES_HOST": "db.example.test",
            "DJANGO_ALLOWED_HOSTS": "api.example.test",
            "CORS_ALLOWED_ORIGINS": "https://app.example.test",
            "CSRF_TRUSTED_ORIGINS": "https://api.example.test",
        }

        errors = validate_production_environment(env)

        self.assertTrue(any("POSTGRES_USER" in error for error in errors))
        self.assertTrue(any("POSTGRES_PASSWORD" in error for error in errors))

        env.update(POSTGRES_USER="app", POSTGRES_PASSWORD="secure-db-password")
        self.assertEqual(validate_production_environment(env), [])

    def test_production_rejects_unsafe_defaults_and_missing_origins(self):
        env = {
            "DJANGO_DEBUG": "0",
            "DJANGO_SECRET_KEY": "unsafe-development-key",
            "DJANGO_ALLOWED_HOSTS": ".vercel.app",
        }

        errors = validate_production_environment(env)

        self.assertTrue(any("DJANGO_SECRET_KEY" in error for error in errors))
        self.assertTrue(any("PostgreSQL" in error for error in errors))
        self.assertTrue(any("DJANGO_ALLOWED_HOSTS" in error for error in errors))
        self.assertTrue(any("CORS_ALLOWED_ORIGINS" in error for error in errors))
