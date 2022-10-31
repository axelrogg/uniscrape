from typing import Generator
import pandas as pd
import scrapy
from scrapy.http.response.html import HtmlResponse

from chi.items import ClassCharacter, ClassItem, DepartmentItem
from chi.langs import LANGS

ScrapyRequestGenerator = Generator[scrapy.Request, None, None]


class UvigoSpider(scrapy.Spider):
    name = "uvigo_spider"
    urls = [
        'https://secretaria.uvigo.gal/docnet-nuevo/guia_docent/',
        'https://www.uvigo.gal/es/estudiar/organizacion-academica/centros'
    ]

    def start_requests(self) -> ScrapyRequestGenerator:

        yield scrapy.Request(url=self.urls[0], callback=self.parse)
        #for i, url in enumerate(self.urls):
        #    if i == 0:
        #        yield scrapy.Request(url=url, callback=self.parse)
        #    else:
        #        yield scrapy.Request(url=url, callback=self.parse_centres)

    def parse(self, response: HtmlResponse, **kwargs) -> ScrapyRequestGenerator:

        sel = response.xpath('//div[@id="menu"]/a//@href')
        department_urls = [
            response.url + link[2:] for link in sel.getall() if
            'centre' and './' in link
        ]

        for url in department_urls:
            yield scrapy.Request(url, self.parse_departments)

    def parse_departments(self,
                          response: HtmlResponse) -> ScrapyRequestGenerator:

        sel = response.xpath('//div[@id="menu"]/a[@class="subapartat"]//@href')

        classes_url_additive = '&consulta=assignatures'
        degrees_urls = [
            self.urls[0] + link + classes_url_additive for link in sel.getall()
        ]

        for url in degrees_urls:
            yield scrapy.Request(url, self.parse_degrees)

    def parse_degrees(self, response: HtmlResponse) -> ScrapyRequestGenerator:

        sel = response.xpath('//table[@class="Verdana"]')
        classes_sel = sel.xpath('./tr/td[@class="Verdana"]/a//@href')
        classes_urls = [self.urls[0] + link + '&idioma=gal' for link in
                        classes_sel.getall()]

        for url in classes_urls:
            yield scrapy.Request(url, self.parse_classes)

    def parse_classes(self, response: HtmlResponse) -> ScrapyRequestGenerator:

        if 'O formato do código de asingatura non é correcto' in response.text:
            return

        def get_class_attrs_df(rp: HtmlResponse):

            dframes = pd.read_html(rp.url)
            # indx_len_dfs = [(idx, len(df)) for idx, df in enumerate(dframes)]
            return dframes[5]

        attrs_df = get_class_attrs_df(response)

        try:
            class_name = attrs_df[1][2]
        except KeyError:
            self.logger.error('CLASS: %s', response.url)
            self.logger.error(attrs_df)
            raise KeyError

        try:
            degree_name = attrs_df[1][3]
        except KeyError:
            self.logger.error('DEGREE %s', response.url)
            self.logger.error(attrs_df)
            raise KeyError

        # class descriptors are credits, character, year, semester
        class_descriptors = []
        for i in attrs_df:
            if i == 0: continue
            for j in range(len(attrs_df.columns)):
                if j == 4 and not pd.isna(attrs_df[i][j]):
                    class_descriptors.append(attrs_df[i][j + 1])

        class_credits = float(class_descriptors[0])
        class_character = class_descriptors[1]
        class_year = int(class_descriptors[2])

        if class_character == 'OP':
            class_character_type = ClassCharacter.OPTIONAL.value
        else:
            class_character_type = ClassCharacter.MANDATORY.value

        class_semester = class_descriptors[3]
        if class_semester != 'An':
            class_semester = int(class_semester[0])

        department_sel = response.xpath('//span[@class="fontheader10"]//text()')
        department_name = department_sel.get().strip()

        sel = response.xpath(
            '//td[@class="mainfons2"][contains(@colspan, "4")]')
        langs = []
        professors = []

        for i, field in enumerate(sel):

            if i == 1:
                lang_tbl_sel = field.xpath('./table[@class="Verdana"]')
                lang_sel = lang_tbl_sel.xpath('./tr/td//text()')

                for lang in lang_sel.getall():
                    if ('#' or 'Outros') in lang: continue

                    for key, val in LANGS.items():
                        if lang.lower() in val:
                            langs.append(key)

            elif i == 4:
                prof_tbl_sel = field.xpath('./table[@class="Verdana"]')
                prof_sel = prof_tbl_sel.xpath('./tr/td//text()')

                for professor in prof_sel.getall():
                    name_list = professor.split(', ')
                    name_list.reverse()
                    name = ' '.join(name_list)
                    if name not in professors:
                        professors.append(name)

            else:
                continue

        sel = response.xpath(
            '//td[@class="mainfons2"][contains(@colspan, "2")]')
        for i, field in enumerate(sel):
            if i == 1:
                coord_tbl_sel = field.xpath('./table[@class="Verdana"]')
                coord_sel = coord_tbl_sel.xpath('./tr/td//text()')

                for coordinator in coord_sel.getall():
                    name_list = coordinator.split(', ')
                    name_list.reverse()
                    name = ' '.join(name_list)
                    if name not in professors:
                        professors.append(name)
            else:
                continue

        class_item = ClassItem(
            department=department_name,
            degrees=[degree_name],
            name=class_name,
            credits=class_credits,
            character=class_character,
            character_type=class_character_type,
            year=class_year,
            semester=class_semester,
            langs=langs,
            professors=professors,
        )

        self.logger.info("Found class item at <%s>: '%s'", response.url,
                         class_item)

        yield class_item

    #def parse_centres(self, response: HtmlResponse):

    #    links_found = []

    #    sel = response.xpath('//h4[@class="icon-arrow-carrot-right"]')

    #    for h4 in sel:
    #        a_sel = h4.xpath('./a')
    #        link = a_sel.xpath('./@href').get()
    #        if (
    #            ('centro' or 'escola' or 'facultade' or 'instituto') in link and
    #            link not in links_found
    #        ):
    #            links_found.append(link)

    #    uvigo_main_url = 'https://www.uvigo.gal'
    #    for link in links_found:
    #        yield scrapy.Request(
    #            url=f'{uvigo_main_url + link}',
    #            callback=self.parse_centre_department
    #        )

    #def parse_centre_department(self, response):

    #    department_sel = response.xpath('//h1[@class="m-b-20"]')
    #    department_name = department_sel.xpath('./text()').get().strip()

    #    address_sel = response.xpath('//div[@class="address"]/div')
    #    location = []
    #    for i, field in enumerate(address_sel):
    #        location_data = field.xpath('./text()').get().strip()
    #        if i == 1:
    #            location.append(location_data[4:])
    #            continue
    #        location.append(location_data)

    #    email = response.xpath(
    #        '//div[@class="text-black"]/a//text()'
    #    ).get()

    #    if isinstance(email, str):
    #        email = email.strip()
    #    else:
    #        email = None
    #        self.logger.error(
    #            f"Email not found for department: {department_name}. "
    #            f"Link: {response.url}"
    #        )

    #    phoneno = response.xpath(
    #        '//div[@class="icon-phone text-black"]/a//text()'
    #    ).get()

    #    if isinstance(phoneno, str):
    #        phoneno = phoneno.strip()
    #    else:
    #        phoneno = None
    #        self.logger.error(
    #            f"Phone number not found for department: {department_name}. "
    #            f"Link: {response.url}"
    #        )

    #    yield DepartmentItem(
    #        name=department_name,
    #        location=location,
    #        email=email,
    #        phoneno=phoneno
    #    )
