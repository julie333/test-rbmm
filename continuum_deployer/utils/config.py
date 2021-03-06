class SettingValue:

    def __init__(self, value, description='', default=False):
        self.description = description
        self.value = value
        self.default = default


class Setting:

    def __init__(self, name, options, value=None, description=''):
        self.name = name
        self.description = description
        self.value = value
        self.options = options

    def get_options(self):
        return self.options

    def set_value(self, value: SettingValue):
        self.value = value

    def get_value(self):
        if self.value is None:
            return self.get_default()
        else:
            return self.value

    def get_default(self):
        for option in self.options:
            if option.default:
                return option


class Config:

    def __init__(self, settings):
        self.settings = Config._settings_to_dict(settings)

    @staticmethod
    def _settings_to_dict(settings):
        _result = dict()
        for setting in settings:
            _result[setting.name] = setting
        return _result

    def add_setting(self, setting: Setting):
        self.settings[setting.name] = setting

    def get_settings(self):
        _settings = []
        for key in self.settings:
            _settings.append(self.settings[key])
        return _settings

    def get_setting(self, name):
        return self.settings.get(name)
