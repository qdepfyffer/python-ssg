import os
import shutil

from functions import rcopy, r_generate_page, generate_page


dir_static = "./static"
dir_public = "./public"
dir_content = "./content"
template_path = "./template.html"


def main():
    print("Deleting public directory...")
    if os.path.exists(dir_public):
        shutil.rmtree(dir_public)

    print("Copying static files to public directory...")
    rcopy(dir_static, dir_public)

    r_generate_page(dir_content, template_path, dir_public)
    

    


if __name__ == "__main__":
    main()