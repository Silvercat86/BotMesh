from plugins.birthday.plugin import BirthdayPlugin
from plugins.clever_shma.plugin import CleverShmaPlugin
from plugins.compliment.plugin import ComplimentPlugin
from plugins.employee_info.plugin import EmployeeInfoPlugin
from plugins.march8.plugin import March8Plugin
from plugins.memes.plugin import MemePlugin
from plugins.start.plugin import StartPlugin
from plugins.welcome.plugin import WelcomePlugin
from plugins.work_experience.plugin import WorkExperiencePlugin
from core.base_plugin import BasePlugin


from services.people_directory import PeopleDirectoryService
from core.base_service import BaseService


PLUGIN_REGISTRY : dict[str, type[BasePlugin]] = {
    "birthday_plugin": BirthdayPlugin,
    "clever_shma_plugin": CleverShmaPlugin,
    "compliment_plugin": ComplimentPlugin,
    "employee_info_plugin": EmployeeInfoPlugin,
    "march8_plugin": March8Plugin,
    "meme_plugin": MemePlugin,
    "start_plugin": StartPlugin,
    "welcome_plugin": WelcomePlugin,
    "work_experience_plugin": WorkExperiencePlugin,

}

SERVICE_REGISTRY : dict[str,type[BaseService]] = {
    "people_directory_service": PeopleDirectoryService,
}