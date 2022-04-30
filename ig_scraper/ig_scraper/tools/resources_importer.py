import os
import json
from .documents_finder import DocumentsFinder

class ResourcesImporter:

    #Resources folder directory
    resources_dir = os.path.abspath(os.curdir) + "\\resources"


    #Imports profiles credentials from JSON File
    def importProfilesFromJSON(self):
        users_to_scrape = []
        file_directory = self.resources_dir + "\\BusinessProfiles.json"
        with open(file_directory, encoding='utf8') as json_file:
            data = json.load(json_file)
            for profile in data["Profiles"]:
                users_to_scrape.append(profile["Id"])
        return users_to_scrape


    #Imports profiles credentials from database
    #Use the appropriate find method for your needs
    def importProfilesFromDatabase(self):
        return list(DocumentsFinder.findDocuments(DocumentsFinder, {}))