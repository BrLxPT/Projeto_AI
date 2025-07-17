from selenium import webdriver
from selenium.webdriver.common.keys import Keys

def fill_web_form(params):
    driver = webdriver.Firefox()
    driver.get(params["url"])
    
    for field in params["fields"]:
        element = driver.find_element("name", field["name"])
        element.send_keys(field["value"])
    
    if params.get("submit"):
        driver.find_element("xpath", params["submit_xpath"]).click()
    
    result = driver.page_source
    driver.quit()
    return result

def register():
    return {
        "name": "web_automation",
        "description": "Automação de navegador e preenchimento de formulários",
        "actions": {
            "web_form_fill": {
                "description": "Preencher formulários web automaticamente",
                "parameters": {
                    "url": "string",
                    "fields": [{"name": "string", "value": "string"}],
                    "submit": "boolean",
                    "submit_xpath": "string"
                },
                "execute": fill_web_form
            }
        }
    }