class FinTechException(Exception):
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class InsufficientFunds(FinTechException):
    def __init__(self, available: float, required: float):
        self.available = available
        self.required = required
        super().__init__(
            f"Insufficient funds: available {available}, required {required}",
            "INSUFFICIENT_FUNDS"
        )


class PaymentProviderError(FinTechException):
    def __init__(self, provider: str, message: str):
        self.provider = provider
        super().__init__(f"{provider}: {message}", "PAYMENT_PROVIDER_ERROR")


class PaymentNotFoundError(FinTechException):
    def __init__(self, payment_id: str):
        self.payment_id = payment_id
        super().__init__(f"Payment not found: {payment_id}", "PAYMENT_NOT_FOUND")


class InvalidPaymentStatusError(FinTechException):
    def __init__(self, current_status: str, operation: str):
        self.current_status = current_status
        self.operation = operation
        super().__init__(
            f"Cannot perform '{operation}' on payment with status '{current_status}'",
            "INVALID_PAYMENT_STATUS"
        )


class WebhookValidationError(FinTechException):
    def __init__(self, message: str = "Invalid webhook signature"):
        super().__init__(message, "WEBHOOK_VALIDATION_ERROR")


class AuthenticationError(FinTechException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR")


class AuthorizationError(FinTechException):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, "AUTHORIZATION_ERROR")


class AccountNotFoundError(FinTechException):
    def __init__(self, account_id: str):
        self.account_id = account_id
        super().__init__(f"Account not found: {account_id}", "ACCOUNT_NOT_FOUND")


class TransactionError(FinTechException):
    def __init__(self, message: str):
        super().__init__(message, "TRANSACTION_ERROR")
