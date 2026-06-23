# converters.py
class ReceiptCodeConverter:
    regex = r'REC-\d{8}-[A-F0-9]{6}'

    def to_python(self, value):
        return str(value)

    def to_url(self, value):
        return str(value)