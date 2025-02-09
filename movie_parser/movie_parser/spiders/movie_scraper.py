from urllib.parse import urljoin
import scrapy
import re  

class MoviesInfoParser(scrapy.Spider):
    name = "movie_scraper"
    start_urls = ["https://ru.wikipedia.org/wiki/Категория:Фильмы_по_алфавиту"]
    custom_settings = {'ROBOTSTXT_OBEY': False}

    def parse(self, response):
        # Получаем ссылки на страницы фильмов
        movie_page_links = response.xpath("//*[@id='mw-pages']//li/a/@href").getall()
        for page in movie_page_links: 
            page_link = response.urljoin(page)  
            yield response.follow(page_link, self.info_parse)

        next_page_link = response.xpath("//a[contains(text(), 'Следующая страница')]/@href").extract_first()
        if next_page_link:
            yield response.follow(response.urljoin(next_page_link), self.parse)

    def info_parse(self, response):
        movie_info = {'title': "Неизвестно", 'genres': [], 'year': "Неизвестно", 'director': [], 'country': []}

        # Извлекаем название фильма
        title = response.css("th.infobox-above::text").get()
        if title:
            movie_info['title'] = title.strip()

        # Парсим таблицу с информацией о фильме
        for row in response.xpath("//table[contains(@class, 'infobox')]//tr"):
            attribute = row.xpath("th//text()").get()
            if attribute:
                attribute = attribute.strip()
            else:
                continue

            values = [line.strip().replace(',', '') for line in row.xpath("td//text()").getall() if line.strip()]
            filtered_values = [value for value in values if not value.startswith('[') and value != '']
            value = ", ".join(filtered_values)

            if 'Жанр' in attribute or 'Жанры' in attribute:
                movie_info['genres'] = [genre.strip() for genre in value.split(",") if len(genre.strip()) > 2]
            elif attribute in ['Режиссёр', 'Режиссёры']:
                cleaned_value = re.sub(r'<[^>]+>', '', value)
                cleaned_value = re.sub(r'[{}#]', '', cleaned_value)
                movie_info['director'] = [director.strip() for director in cleaned_value.split(",") if len(director.strip()) > 2]
            elif attribute in ['Страна', 'Страны']:
                movie_info['country'] = [country.strip() for country in value.split(",") if len(country.strip()) > 2]
            elif attribute == 'Год':
                movie_info['year'] = value if value else "Неизвестно"

        # Если поля пустые, заменяем их значением "Неизвестно"
        for key in ['genres', 'director', 'country']:
            if not movie_info[key]:
                movie_info[key] = ["Неизвестно"]

        yield {
            'title': movie_info['title'],
            'genres': ", ".join(movie_info['genres']),
            'director': ", ".join(movie_info['director']),
            'country': ", ".join(movie_info['country']),
            'year': movie_info['year'],
        }
