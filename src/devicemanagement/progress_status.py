"""Status text with optional backup-category metadata; remains string-compatible."""


class OperationStatus(str):
    def __new__(cls, text, category):
        instance = super().__new__(cls, text)
        instance.category = category
        return instance


class BackupStatus(OperationStatus):
    pass
