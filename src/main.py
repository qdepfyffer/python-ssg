import os
import sys
import shutil

from functions import rcopy, r_generate_page


def main():

    dir_static = "./static"
    dir_public = "./docs"
    dir_content = "./content"
    template_path = "./template.html"

    basepath = sys.argv[1] if len(sys.argv) >= 2 else "/"

    print("Deleting public directory...")
    if os.path.exists(dir_public):
        shutil.rmtree(dir_public)

    print("Copying static files to public directory...")
    rcopy(dir_static, dir_public)

    r_generate_page(basepath, dir_content, template_path, dir_public)
    
    
if __name__ == "__main__":
    main()