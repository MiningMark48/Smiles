class VirtualHelpers:
    @staticmethod
    def prepare_id(uuid: str):
        return uuid.lower().replace(" ", "_")
