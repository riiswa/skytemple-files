#  Copyright 2020 Parakoopa
#
#  This file is part of SkyTemple.
#
#  SkyTemple is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  SkyTemple is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with SkyTemple.  If not, see <https://www.gnu.org/licenses/>.
import re
from typing import Union, TypeVar, Iterable

from skytemple_files.common.ppmdu_config.script_data import *
from explorerscript.ssb_converting.ssb_data_types import SsbOpParamConstant, DungeonModeConstants

NULL = 'NULL'
PREFIX_DIRECTION = 'DIRECTION_'
PREFIX_PROCESS_SPECIAL = 'PROCESS_SPECIAL_'
PREFIX_MENU = 'MENU_'
PREFIX_LEVEL = 'LEVEL_'
PREFIX_FACE_POS = 'FACE_POS_'
PREFIX_FACE = 'FACE_'
PREFIX_OBJECT = 'OBJECT_'
PREFIX_ACTOR = 'ACTOR_'
PREFIX_CORO = 'CORO_'
PREFIX_VAR = 'VAR_'
PREFIX_OBJECT_NULL = PREFIX_OBJECT + NULL + '_'
PREFIX_DMODE = 'DMODE_'
CAMEL_REGEX = re.compile(r'(?<!^)(?=[A-Z])')


class DungeonMode(Enum):
    CLOSED = 0
    OPEN = 1
    REQUEST = 2


SsbConstantPmdScriptMappable = Union[
    Pmd2ScriptEntity, Pmd2ScriptObject, Pmd2ScriptRoutine,
    Pmd2ScriptFaceName, Pmd2ScriptFacePositionMode, Pmd2ScriptGameVar,
    Pmd2ScriptLevel, Pmd2ScriptMenu, Pmd2ScriptSpecial, Pmd2ScriptDirection,
    DungeonMode
]
T = TypeVar('T')


class SsbConstant(SsbOpParamConstant):
    """
    Class to map entries from the PPMDU script config (and other sources)
    to constants for use in ssb representations.

    Pmd2Script* objects can be converted into this by using create_for.

    The representation as a string can be retrieved using str(self) or repr(self).

    The constructor can be used with any string that this class represents,
    (and an instance of Pmd2ScriptData) and be converted back with convert_to_script_entity.
    Giving it an unknown constant_as_string value will aise a ValueError.
    """
    def __init__(
            self, constant_as_string: str,
            script_data: Pmd2ScriptData = None, value: SsbConstantPmdScriptMappable = None
    ):
        """Either script_data or the value argument must be present."""
        super().__init__(constant_as_string)

        # Init value if not set
        if not value:
            if not script_data:
                raise ValueError(f"Either value or script_data must be provided.")
            value = self._map_back(constant_as_string, script_data)

        self.value = value
        self.name = constant_as_string

    @classmethod
    def create_for(cls, value: SsbConstantPmdScriptMappable) -> 'SsbConstant':
        if isinstance(value, Pmd2ScriptEntity):
            return cls(PREFIX_ACTOR + value.name, value=value)
        elif isinstance(value, Pmd2ScriptObject):
            if value.name == NULL:
                return cls(PREFIX_OBJECT_NULL + str(value.id), value=value)
            return cls(PREFIX_OBJECT + value.name.upper(), value=value)
        elif isinstance(value, Pmd2ScriptRoutine):
            return cls(PREFIX_CORO + value.name, value=value)
        elif isinstance(value, Pmd2ScriptFaceName):
            return cls(PREFIX_FACE + value.name, value=value)
        elif isinstance(value, Pmd2ScriptFacePositionMode):
            return cls(PREFIX_FACE_POS + value.name.upper(), value=value)
        elif isinstance(value, Pmd2ScriptGameVar):
            return cls(PREFIX_VAR + value.name, value=value)
        elif isinstance(value, Pmd2ScriptLevel):
            return cls(PREFIX_LEVEL + value.name, value=value)
        elif isinstance(value, Pmd2ScriptMenu):
            return cls(PREFIX_MENU + cls._cvrt_camel(value.name), value=value)
        elif isinstance(value, Pmd2ScriptSpecial):
            return cls(PREFIX_PROCESS_SPECIAL + cls._cvrt_camel(value.name), value=value)
        elif isinstance(value, Pmd2ScriptDirection):
            return cls(PREFIX_DIRECTION + value.name.upper(), value=value)
        elif isinstance(value, DungeonMode):
            return cls(PREFIX_DMODE + value.name, value=value)
        raise TypeError(f"value must be of type SsbConstantPmdScriptMappable.")

    @classmethod
    def _map_back(cls, constant_as_string: str, script_data: Pmd2ScriptData) -> SsbConstantPmdScriptMappable:
        """Inverse of create_for."""
        try:
            if constant_as_string.startswith(PREFIX_ACTOR):
                return script_data.level_entities__by_name[constant_as_string[len(PREFIX_ACTOR):]]
            elif constant_as_string.startswith(PREFIX_OBJECT_NULL):
                obj = script_data.objects__by_id[constant_as_string[len(PREFIX_OBJECT_NULL):]]
                if obj.name != NULL:
                    raise KeyError(obj.id)
                return obj
            elif constant_as_string.startswith(PREFIX_OBJECT):
                return cls._in_dict_insensitive(script_data.objects__by_name, constant_as_string[len(PREFIX_OBJECT):])
            elif constant_as_string.startswith(PREFIX_CORO):
                return script_data.common_routine_info__by_name[constant_as_string[len(PREFIX_CORO):]]
            elif constant_as_string.startswith(PREFIX_FACE_POS):
                return cls._in_dict_insensitive(script_data.face_position_modes__by_name, constant_as_string[len(PREFIX_FACE_POS):])
            elif constant_as_string.startswith(PREFIX_FACE):
                return script_data.face_names__by_name[constant_as_string[len(PREFIX_FACE):]]
            elif constant_as_string.startswith(PREFIX_VAR):
                return script_data.game_variables__by_name[constant_as_string[len(PREFIX_VAR):]]
            elif constant_as_string.startswith(PREFIX_LEVEL):
                return script_data.level_list__by_name[constant_as_string[len(PREFIX_LEVEL):]]
            elif constant_as_string.startswith(PREFIX_MENU):
                return cls._in_dict_insensitive(
                    script_data.menus__by_name,
                    cls._cvrt_camel_inverse(constant_as_string[len(PREFIX_MENU):])
                )
            elif constant_as_string.startswith(PREFIX_PROCESS_SPECIAL):
                return cls._in_dict_insensitive(
                    script_data.process_specials__by_name,
                    cls._cvrt_camel_inverse(constant_as_string[len(PREFIX_PROCESS_SPECIAL):])
                )
            elif constant_as_string.startswith(PREFIX_DIRECTION):
                return cls._in_dict_insensitive(script_data.directions__by_name, constant_as_string[len(PREFIX_DIRECTION):])
        except KeyError:
            raise ValueError(f"Unknown constant {constant_as_string}.")
        raise ValueError(f"Unknown constant {constant_as_string}.")

    @staticmethod
    def _cvrt_camel(string) -> str:
        return CAMEL_REGEX.sub('_', string).upper()

    @staticmethod
    def _cvrt_camel_inverse(string) -> str:
        return ''.join(word.title() for word in string.split('_'))

    @staticmethod
    def _in_dict_insensitive(d: Dict[str, T], k: str) -> T:
        """Case insensitive access to a string indexed dict"""
        for dk, dv in d.items():
            if dk.lower() == k.lower():
                return dv
        raise KeyError(k)

    def convert_to_script_entity(self):
        return self.value

    def __repr__(self):
        return str(self)

    @classmethod
    def collect_all(cls, rom_data: Pmd2ScriptData) -> Iterable['SsbConstant']:
        """Collects all possible constants from the given ROM data"""
        for x in rom_data.level_entities:
            yield cls.create_for(x)
        for x in rom_data.objects:
            yield cls.create_for(x)
        for x in rom_data.common_routine_info:
            yield cls.create_for(x)
        for x in rom_data.face_names:
            yield cls.create_for(x)
        for x in rom_data.face_position_modes:
            yield cls.create_for(x)
        for x in rom_data.game_variables:
            yield cls.create_for(x)
        for x in rom_data.level_list:
            yield cls.create_for(x)
        for x in rom_data.menus:
            yield cls.create_for(x)
        for x in rom_data.process_specials:
            yield cls.create_for(x)
        for x in rom_data.directions.values():
            yield cls.create_for(x)
        for x in [DungeonMode.CLOSED, DungeonMode.OPEN, DungeonMode.REQUEST]:
            yield cls.create_for(x)

    @classmethod
    def get_dungeon_mode_constants(cls):
        return DungeonModeConstants(
            PREFIX_DMODE + DungeonMode.OPEN.name,
            PREFIX_DMODE + DungeonMode.REQUEST.name,
            PREFIX_DMODE + DungeonMode.CLOSED.name
        )

