import pandas as pd

def clean_data(df: pd.DataFrame):
    df['siret'] = df['siret'].astype(str)
    df['dateDebut'] = pd.to_datetime(df['dateDebut'], errors='coerce')
    df['etat'] = df['etat'].astype(str).str.slice(0, 2)
    df['code_ape'] = df['code_ape'].astype(str)
    df['code_commune'] = df['code_commune'].astype(str).str.zfill(5)
    df['code_tranche'] = df['code_tranche'].astype(str)
    

    # df = df.rename(columns={
    #     'dateDebut': 'valid_from',
    #     'code_tranche': 'tranche_effectif'
    # })
    
    return df