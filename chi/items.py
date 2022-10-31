# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from dataclasses import dataclass, field
from enum import Enum


class ClassCharacter(Enum):
    MANDATORY = 'mandatory'
    OPTIONAL = 'optional'


@dataclass
class ClassItem:
    department: str
    degrees: list[str]
    name: str
    credits: float
    character: str
    character_type: str
    year: int
    semester: int | str
    langs: list[str]
    professors: list[str]


@dataclass
class DegreeItem:
    department: str
    name: str
    type: str


@dataclass
class DepartmentItem:
    name: str
    location: list[str]
    email: str | None = None
    phoneno: str | None = None
    degrees: list[DegreeItem] = field(default_factory=list)


class DegreeType(Enum):
    BACHELORS = 'bachelors'
    MASTERS = 'masters'
    DOCTORATE = 'doctorate'


@dataclass
class UniversityItem:
    name: str
    country: str
    city: str
    classes: list[ClassItem] = field(default_factory=list)
    departments: list[DepartmentItem] = field(default_factory=list)
    #degrees: list[DegreeItem] = field(default_factory=list)


