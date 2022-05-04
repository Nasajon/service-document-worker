import os
import shutil
import time
import stat

from app.settings import NEXUS_USER, NEXUS_PASSWORD, DOCKER_HUB_USER, DOCKER_HUB_PASSWORD, logger


class BuildService:

    def __init__(self):
        self.nexus_user = NEXUS_USER
        self.nexus_password = NEXUS_PASSWORD
        self.docker_hub_user = DOCKER_HUB_USER
        self.docker_hub_password = DOCKER_HUB_PASSWORD
        self.project_root_path = os.path.abspath(".\..")
        self.working_dir = os.path.join(self.project_root_path, f"temp\\{int(time.time())}")

    def execute(self, branch):
        # Restart scheduled shutdown (if set) to set a "timeout" in case anything goes wrong
        logger.info(f"Scheduling shutdown")
        self.cancel_scheduled_logoff()
        self.schedule_logoff()

        # Download and checkout to branch
        logger.info(f"Cloning and checking out to branch {branch}")
        self.checkout_branch(branch)

        # Download service document executable
        logger.info("Download Service Document Executable")
        self.download_service_document()

        # Build and upload image
        image_name = self.build_image(branch)

        self.upload_image(image_name)

        # Cleaning temporary files
        logger.info("Cleaning temporary files")
        self.clear_temporary_path()

        return image_name
    
    def checkout_branch(self, branch):
        os.system(f"git clone git@github.com:Nasajon/service-document-worker.git {self.working_dir} --recursive")
        os.system(f"git checkout {branch}")

    def download_service_document(self):
        os.chdir(self.working_dir)
        # TODO: baixar uma versão do service document equivalente a da branch sendo construída
        os.system(f"curl.exe -u  {self.nexus_user}:{self.nexus_password} -X GET https://nexus.nasajon.com.br/repository/erp/br/com/nasajon/nsjServiceDocumentEngine/2.2203.0.1786/nsjServiceDocumentEngine-2.2203.0.1786.exe --output nsjServiceDocumentEngine.exe")

    def build_image(self, branch):
        os.chdir(self.working_dir)
        version = str(time.localtime().tm_mday) + str(time.localtime().tm_hour) + str(time.localtime().tm_min)
        image_name = f"arquiteturansj/servicedocumentworker:{branch}-{version}"
        logger.info(f"Building image {image_name}")
        os.system(f"docker build -t {image_name} .")
        return image_name

    def upload_image(self, image_name):
        os.chdir(self.working_dir)
        logger.info("Logging to docker hub.")
        os.system(f"docker login -u {self.docker_hub_user} -p {self.docker_hub_password}")

        logger.info(f"Pushing image {image_name} to docker hub.")
        os.system(f"docker push {image_name}")

        logger.info(f"Deleting image {image_name} locally.")
        os.system(f"docker rmi {image_name}")
    
    def schedule_logoff(self):
        # Schedule windows to shutdown in 30 minutes
        os.system("shutdown /s /f /t 1800")

    def cancel_scheduled_logoff(self):
        os.system("shutdown /a")
    
    def clear_temporary_path(self):
        def remove_readonly(func, path, excinfo):
            os.chmod(path, stat.S_IWRITE)
            func(path)
        shutil.rmtree(self.working_dir, onerror=remove_readonly)
