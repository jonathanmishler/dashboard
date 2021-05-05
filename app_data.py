from pathlib import Path
from typing import Optional, List
import pandas as pd
from geopy import MapBox, location
from geopy.extra.rate_limiter import RateLimiter

from config import AppSettings


def load():
    column_dtypes = {
        "Customer": "string",
        "Address": "string",
        "Q": "float64",
        "Item": "category",
        "$ Amount": "float64",
        "Notes/PO": "string",
        "Invoice/SR": "string",
        "Check/Payment": "category",
        "PayNumber": "string",
        "Zone": "category",
        "DelType": "category",
        "Owner": "category",
        "Week": "category",
        "Month": "category",
        "Year": "category",
        "Type": "category",
        "Quarter": "category",
        "O Q and Y": "string",
        "Product": "category",
        "Name": "category",
        "UPC": "category",
        "Can Type": "category",
        "Pk": "category",
    }

    df = pd.read_csv(
        "Customer Power Stats.csv", dtype=column_dtypes, parse_dates=["Date"]
    )
    df.Customer = df.Customer.str.strip()
    return df


def create_chain_list(df, chains: list):
    for chain_name in chains:        
        df.loc[df.Customer.str.startswith(chain_name), 'chain'] = chain_name
    sel = df['chain'].isin(chains)
    chain_list = df[sel].drop_duplicates('Customer').loc[:,['Customer', 'Address', 'chain']]
    chain_list['Address'] = chain_list.Address.str.strip().str.replace("\n",", ")
    with GeoLocator() as geocoder:
        chain_list[["norm_address", "lat", "lon"]] = chain_list.apply(geocoder.get_location, axis=1)
    return chain_list



class GeoLocator:
    LOCAL_DATA_FILE = "customer_locations.csv"
    LOCATION_SCHEMA = {
        "Customer": "string",
        "Address": "string",
        "norm_address": "string",
        "lat": "float64",
        "lon": "float64",
    }

    def __init__(self):
        self.local_data_path = Path("customer_locations.csv")
        self.locations = self.get_local_data()
        self.new_locations = list()
        self.app_settings = AppSettings()
        self.setup_geocoder()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.save()

    def get_local_data(self) -> Optional[pd.DataFrame]:
        df = None
        if self.local_data_path.exists():
            df = pd.read_csv(
                self.local_data_path,
                dtype=self.LOCATION_SCHEMA,
            )
            df = df.drop_duplicates("Customer", keep=False)
        return df

    def setup_geocoder(self) -> None:
        self.geocoder = RateLimiter(
            MapBox(api_key=self.app_settings.mapbox_api_key).geocode,
            min_delay_seconds=1,
        )

    def geocode(self, address: str) -> tuple:
        geoloc = self.geocoder(address)

        return geoloc.address, geoloc.latitude, geoloc.longitude

    def get_location(self, row: pd.Series) -> List[dict]:
        geoloc = self.search_local_data(row.Customer)
        if geoloc is None:
            geoloc = self.geocode(row.Address)
            self.new_locations.append(
                {
                    "Customer": row.customer,
                    "Address": row.address,
                    "norm_address": geoloc[0],
                    "lat": geoloc[1],
                    "lon": geoloc[2],
                }
            )
        return pd.Series(geoloc)

    def add_locations(self) -> None:
        if self.locations is None:
            self.locations = pd.DataFrame(self.new_locations)
        else:
            self.locations = pd.concat([self.locations, pd.DataFrame(self.new_locations)])

    def search_local_data(self, customer: str) -> Optional[tuple]:
        geoloc = None
        if self.locations is not None:
            find_customer = self.locations["Customer"] == customer
            if find_customer.sum() == 1:
                geoloc = self.locations.loc[
                    find_customer, ["norm_address", "lat", "lon"]
                ]
                geoloc = tuple(geoloc.values[0])
        return geoloc

    def save(self) -> None:
        if self.new_locations:
            self.add_locations()
        if self.locations is not None:
            self.locations.to_csv(self.local_data_path, index=False)
