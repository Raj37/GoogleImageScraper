import os
import time
import requests
from selenium import webdriver
from flask_cors import CORS,cross_origin
from flask import Flask, render_template, request,jsonify


#DRIVER_PATH = './chromedriver' #run on local
DRIVER_PATH = os.environ.get("CHROMEDRIVER_PATH")
#search_term = 'laptop'



# import request
app = Flask(__name__) # initialising the flask app with the name 'app'

#response = 'Welcome!'


@app.route('/')  # route for redirecting to the home page
@cross_origin()
def home():
    return render_template('index.html')

@app.route('/showImages') # route to show the images on a webpage
@cross_origin()
def show_images():
    #scraper_object=ImageScrapper() #Instantiating the object of class ImageScrapper
    list_of_jpg_files=list_only_jpg_files('static') # obtaining the list of image files from the static folder
    print(list_of_jpg_files)
    try:
        if(len(list_of_jpg_files)>0): # if there are images present, show them on a wen UI
            print("inside if of show_images() fun")
            return render_template('showImage.html',user_images = list_of_jpg_files)
        else:
            print("inside else of show_images() fun")
            return "Please try with a different string" # show this error message if no images are present in the static folder
    except Exception as e:
        print('no Images found ', e)
        return "Please try with a different string"

@app.route('/searchImages', methods=['GET','POST'])
def searchImages():
    if request.method == 'POST':
        print("entered post")
        keyWord = request.form['keyword'] # assigning the value of the input keyword to the variable keyword
        print("keyWord=>",keyWord)
        # scraper_object = ImageScrapper() # instantiating the class
        print("checking jpg img present or not inside images folder...")
        list_of_jpg_files = list_only_jpg_files('static')  # obtaining the list of image files from the static folder
        print("list_of_jpg_files=>",list_of_jpg_files)
        delete_existing_image(list_of_jpg_files)  # deleting the old image files stored from the previous search
        print("old jpg img deleted successfully")
        print("Downloading for searched image in progress...")
        search_and_download(search_term=keyWord, driver_path=DRIVER_PATH)
        return show_images()  # redirect the control to the show images method

    else:
        return render_template('index.html')


def delete_existing_image(list_of_images):
    for image in list_of_images:
        try:
            os.remove("./static/"+image)
        except Exception as e:
            print('error in deleting:  ',e)
    return 0

def fetch_image_urls(query: str, max_links_to_fetch: int, wd: webdriver, sleep_between_interactions: int = 1):
    def scroll_to_end(wd):
        wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(sleep_between_interactions)

        # build the google query


    search_url = "https://www.google.com/search?safe=off&site=&tbm=isch&source=hp&q={q}&oq={q}&gs_l=img"

    # load the page
    wd.get(search_url.format(q=query))

    image_urls = set()
    image_count = 0
    results_start = 0
    while image_count < max_links_to_fetch:
        scroll_to_end(wd)

        # get all image thumbnail results
        thumbnail_results = wd.find_elements_by_css_selector("img.Q4LuWd")
        number_results = len(thumbnail_results)

        print(f"Found: {number_results} search results. Extracting links from {results_start}:{number_results}")

        for img in thumbnail_results[results_start:number_results]:
            # try to click every thumbnail such that we can get the real image behind it
            try:
                img.click()
                time.sleep(sleep_between_interactions)
            except Exception:
                continue

            # extract image urls
            actual_images = wd.find_elements_by_css_selector('img.n3VNCb')
            for actual_image in actual_images:
                if actual_image.get_attribute('src') and 'http' in actual_image.get_attribute('src'):
                    image_urls.add(actual_image.get_attribute('src'))

            image_count = len(image_urls)

            if len(image_urls) >= max_links_to_fetch:
                print(f"Found: {len(image_urls)} image links, done!")
                break
        else:
            print("Found:", len(image_urls), "image links, looking for more ...")
            time.sleep(30)
            #return
            load_more_button = wd.find_element_by_css_selector(".mye4qd")
            if load_more_button:
                wd.execute_script("document.querySelector('.mye4qd').click();")

        # move the result startpoint further down
        results_start = len(thumbnail_results)

    return image_urls

def persist_image(folder_path:str,url:str, counter):
    try:
        image_content = requests.get(url).content

    except Exception as e:
        print(f"ERROR - Could not download {url} - {e}")

    try:
        f = open(os.path.join(folder_path, 'jpg' + "_" + str(counter) + ".jpg"), 'wb')
        f.write(image_content)
        f.close()
        print(f"SUCCESS - saved {url} - as {folder_path}")
    except Exception as e:
        print(f"ERROR - Could not save {url} - {e}")

def list_only_jpg_files(folder_name):
    list_of_jpg_files=[]
    list_of_files=os.listdir(folder_name)
    print('list of files==')
    print(list_of_files)
    for file in list_of_files:
        name_array= file.split('.')
        if(name_array[1]=='jpg'):
            list_of_jpg_files.append(file)
        else:
            print('filename does not end withn jpg')
    return list_of_jpg_files

def search_and_download(search_term: str, driver_path: str, target_path='./images', number_images=5):
    #target_folder = os.path.join(target_path, '_'.join(search_term.lower().split(' '))) # make the folder name inside images with the search string
    target_folder = './static'
    if not os.path.exists(target_folder):
        os.makedirs(target_folder) # make directory using the target path if it doesn't exist already

    # Chrome driver
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")

    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    #driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)
    # Now you can start using Selenium

    with webdriver.Chrome(executable_path=driver_path, chrome_options=chrome_options) as wd:
        res = fetch_image_urls(search_term, number_images, wd=wd, sleep_between_interactions=0.5)

    counter = 0
    for elem in res:
        persist_image(target_folder, elem, counter)
        counter += 1


# num of images you can pass it from here  by default it's 10 if you are not passing
#number_images = 100

#port = int(os.getenv("PORT"))
if __name__ == "__main__":
    #app.run(host='0.0.0.0', port=port)
    #app.run(host='127.0.0.1', port=8000) # port to run on local machine
    app.run(debug=True) # to run on cloud