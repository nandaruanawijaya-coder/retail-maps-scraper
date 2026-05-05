from dataclasses import dataclass


@dataclass
class District:
    district_id: str
    kelurahan: str
    kecamatan: str
    kabupaten: str
    provinsi: str
    district_name: str = None

    def __post_init__(self):
        if self.district_name is None:
            self.district_name = self.kecamatan
