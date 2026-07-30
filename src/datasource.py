from dataclasses import dataclass
from pathlib import Path
import requests
import config.config as config

@dataclass
class DataSourceResult:
    histo: str | Path
    etab: str | Path

class DataSourceManager:
    def __init__(self, data_dir: str = "data"):
        self.histo_url = config.Urls.histo_etablissements
        self.etab_url = config.Urls.etablissements
        self.data_path = Path(data_dir)
        
    def _test_apis(self) -> bool:
        try:
            res_histo = requests.head(self.histo_url, timeout=5)
            if not res_histo.ok:
                return False
                
            res_etab = requests.head(self.etab_url, timeout=5)
            if not res_etab.ok:
                return False
                
            return True
        except requests.RequestException:
            return False

    def _find_local_file(self, include_keyword: str, exclude_keyword: str = None) -> Path:
        if not self.data_path.exists():
            raise FileNotFoundError(f"Le dossier {self.data_path} n'existe pas.")
            
        for file in self.data_path.iterdir():
            if file.is_file() and include_keyword in file.name:
                if exclude_keyword and exclude_keyword in file.name:
                    continue
                return file
                
        raise FileNotFoundError(f"Aucun fichier correspondant n'a été trouvé dans {self.data_path}")

    def get_source(self) -> DataSourceResult:
        if self._test_apis():
            print("APIs opérationnelles, utilisation des URLs")
            return DataSourceResult(
                histo=self.histo_url,
                etab=self.etab_url
            )
        else:
            print("APIs injoignables, recherche des fichiers locaux")
            histo_file = self._find_local_file("histo")
            etab_file = self._find_local_file("etab", exclude_keyword="histo")
            
            return DataSourceResult(
                histo=histo_file,
                etab=etab_file
            )