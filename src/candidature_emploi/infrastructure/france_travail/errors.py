"""Erreurs techniques classées et présentables sans secret."""


class ProviderError(RuntimeError):
    user_message = "Le service externe est momentanément indisponible."


class ProviderConfigurationError(ProviderError):
    user_message = "La connexion France Travail n’est pas configurée."


class ProviderAuthenticationError(ProviderError):
    user_message = "L’authentification France Travail a échoué."


class ProviderRateLimitError(ProviderError):
    user_message = "Le quota de l’API est temporairement atteint."


class ProviderUnavailableError(ProviderError):
    user_message = "Le service France Travail est momentanément indisponible."


class ProviderRequestError(ProviderError):
    user_message = "Les critères transmis au service sont invalides."


class ProviderResponseError(ProviderError):
    user_message = "La réponse du service est inexploitable."
