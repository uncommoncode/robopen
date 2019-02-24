class GRBL:
    @staticmethod
    def soft_reset():
        return '\x18'

    @staticmethod
    def get_status():
        return '$'

    @staticmethod
    def query_state():
        return '?'

    @staticmethod
    def toggle_run():
        return '~'
