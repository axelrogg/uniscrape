# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
# from itemadapter import ItemAdapter

import json
from typing import Any
from dataclasses import asdict
from scrapy.exceptions import DropItem

from chi.items import (
        ClassItem,
        DegreeItem,
        DegreeType,
        DepartmentItem,
        UniversityItem,
        )


class ChiPipeline:

    def __init__(self):
        self.university = None
        self.department_names = []
        self.degrees = {} # {'department_name': degree_items}

    def open_spider(self, spider):
        self.university = UniversityItem('Universidade de Vigo', 'Spain', 'Vigo')

    def close_spider(self, spider):

        self.university.departments = [
            {'name': depname, 'degrees': degrees} for depname, degrees in self.degrees.items()
        ]
        with open('uvigo.json', encoding='utf-8', mode='w') as f:
            data = json.dumps(asdict(self.university), ensure_ascii=False,
                              indent=2)
            f.write(data)

    def gen_degree_items(
            self, item: Any, degree_names: list[str], department_name: str, spider
        ) -> list[DegreeItem]:

        degree_items: list[DegreeItem] = []
        for degree in degree_names:
            if 'grado' in degree.lower():
                raise DropItem('Spanish degree name: %s. Item: %s', degree, item)
            if 'grao' in degree.lower() or 'grado' in degree.lower():
                degtype = DegreeType.BACHELORS
            elif 'master' in degree.lower() or 'máster' in degree.lower():
                degtype = DegreeType.MASTERS
            else:
                degtype = DegreeType.DOCTORATE
            
            degree_items.append(DegreeItem(department_name, degree, degtype.value))
        return degree_items

    def process_item(self, item: ClassItem | DepartmentItem, spider):

        if isinstance(item, ClassItem):

            if item.department not in self.department_names:
                self.degrees[item.department] = self.gen_degree_items(item, item.degrees, item.department, spider)
                self.department_names.append(item.department)

            else:
                self.degrees[item.department].extend(
                        [
                            degree for degree in 
                            self.gen_degree_items(item, item.degrees, item.department, spider)
                            if degree not in self.degrees[item.department]
                            ]
                        )

            self.university.classes.append(item)

        #elif isinstance(item, DepartmentItem):

        #    if item.name not in self.department_names:
        #        print(f"Unknown department of name: '{item.name}'\nHere's the list of all departments: {self.department_names}")

        #    else:
        #        item.degrees = self.degrees[item.name]
        #        self.university.departments.append(item)

        #    return item

        else:
            raise DropItem('Unrecognized item type. Item: %s, type: %s', item, type(item))
            return item
