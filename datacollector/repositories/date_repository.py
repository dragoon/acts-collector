from datacollector.domain import AssetDataEntry


class DataRepository:
    def __init__(self, db, asset_name: str):
        self.col = db[f"{asset_name}_data"]

    def insert_one(self, entry: AssetDataEntry) -> None:
        self.col.insert_one(entry.to_dict())
