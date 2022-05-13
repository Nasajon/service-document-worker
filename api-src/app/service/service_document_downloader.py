import time
import requests

from requests.auth import HTTPBasicAuth
from xml.etree import ElementTree
from app.settings import NEXUS_USER, NEXUS_PASSWORD, logger


class ServiceDocumentDownloader:

    def __init__(self) -> None:
        self.basic_auth = HTTPBasicAuth(NEXUS_USER, NEXUS_PASSWORD)
        self.nexus_metadata_endpoint = "https://nexus.nasajon.com.br/repository/erp/br/com/nasajon/nsjServiceDocumentEngine/maven-metadata.xml"
        self.nexus_compilation_download_url = "https://nexus.nasajon.com.br/repository/erp/br/com/nasajon/nsjServiceDocumentEngine/{compilation}/nsjServiceDocumentEngine-{compilation}.exe"
        self.metadata = None
    
    def download_latest_version_from_branch_name(self, branch: str, download_abs_path: str):
        # Downloads and parse the metadata
        self.download_parse_metadata()

        # Defines version
        if branch == "master":
            version = "2." + str(time.localtime().tm_year)[-2:] + "{:02d}".format(time.localtime().tm_mon)
        else:
            version = branch.replace("v", "")
        
        # Try to find a compilation
        compilation = self.find_latest_compilation(version)
        
        # Defaults to latest release
        if compilation is None:
            version = "latest"
            compilation = self.find_latest_compilation(version)

        # Downloads asset
        self.download_service_document(compilation, download_abs_path)

        return compilation

    def find_latest_compilation(self, version: str):
        latest_release = self.metadata[2][0].text

        if version == 'latest':
            return latest_release
        
        # Search for all compilations of the given version
        compilations = []
        for ver in self.metadata[2][2]:
            if ver.text.startswith(version):
                compilations.append(ver.text)
        if len(compilations) > 0:
            return compilations[-1]
        
        return None

    def download_parse_metadata(self):
        if self.metadata is not None:
            return self.metadata
        
        response = requests.get(self.nexus_metadata_endpoint, auth=self.basic_auth)
        if response.status_code != 200:
            raise Exception("Could not get metadata from nexus repository")
        
        self.metadata = ElementTree.fromstring(response.text)
    
    def download_service_document(self, compilation: str, download_abs_path: str):
        url = self.nexus_compilation_download_url.format(compilation=compilation)

        response = requests.get(url, auth=self.basic_auth)
        if response.status_code != 200:
            raise Exception("Could not download service document executable")
        
        with open(download_abs_path, "wb") as file:
            file.write(response.content)
