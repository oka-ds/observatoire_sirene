import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
from load import clean_data

load_dotenv()

def load_data(source_table_name: str, target_table_name: str):
    engine = create_engine(os.getenv('DATABASE_URL'))
    df = pd.read_sql(
        # TODO change columns name (here column from table, then rename in clean)
        f"SELECT * FROM {source_table_name}",
        columns=["siret", "dateDebut", "etat", "code_ape", "code_commune", "code_tranche"],
        con=engine
    )
    
    df = clean_data(df)
    
    df = df.sort_values(["siret", "dateDebut"])

    df["cle"] = df["code_ape"].fillna("?") + "|" + df["etat"].fillna("?")
    df["cle_prec"] = df.groupby("siret")["cle"].shift(1)

    fait: pd.DataFrame = df[df["cle"] != df["cle_prec"]].copy()

    fait["valid_from"] = fait["dateDebut"]
    fait["valid_to"]   = fait.groupby("siret")["valid_from"].shift(-1)
    fait["is_current"] = fait["valid_to"].isna()
    
    fait.to_sql(
        name=target_table_name,
        con=engine,
        if_exists='replace',
        index=False,
        chunksize=10000
    )
    print(f"Table {target_table_name} mise à jour avec succès !")