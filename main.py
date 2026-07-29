from ingestion import load_etab
from load import DatabaseManager

def main():
    DatabaseManager()
    load_etab(histo=False, code_dept='69')
    
if __name__ == "__main__":
    main()