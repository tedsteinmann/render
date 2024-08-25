import os
import json
import shutil
import configparser
import frontmatter
import pypandoc

from datetime import date

config = configparser.ConfigParser()
config.read('config.ini') 

content_dir = config.get('paths', 'content_dir', fallback='/content')
output_dir = config.get('paths', 'output_dir', fallback='/output')
template_dir = config.get('paths', 'template_dir', fallback='/templates')
static_dir = config.get('paths', 'static_dir', fallback='/static')

default_template = os.path.join(template_dir, "index.html")

def copy_static_folder():
    """Copy the contents of the static folder to the output directory."""
    destination_dir = os.path.join(output_dir, "static")
    if os.path.exists(static_dir):
        if os.path.exists(destination_dir):
            shutil.rmtree(destination_dir)  # Remove existing static folder in output
        shutil.copytree(static_dir, destination_dir)
        print(f"Copied static folder to {destination_dir}")
    else:
        print("Static folder not found, skipping copy.")

def extract_front_matter(md_file):
    post = frontmatter.load(md_file)
    return post.metadata  # Returns a dictionary of the front matter

def get_extra_properties(config):
    """Extract extra properties from the config.ini file."""
    extra_properties = {}
    if config.has_section('properties'):
        for key, value in config.items('properties'):
            extra_properties[key] = value
    return extra_properties

def load_and_replace_sub_templates(template_content):
    """Dynamically load and replace sub-templates in the main template."""
    for template_file in os.listdir(template_dir):
        if template_file.endswith(".html") and template_file != "default.html":
            placeholder_name = f"${template_file.replace('.html', '')}$"
            sub_template_path = os.path.join(template_dir, template_file)
            with open(sub_template_path, 'r', encoding='utf-8') as f:
                sub_template_content = f.read()
            template_content = template_content.replace(placeholder_name, sub_template_content)
    return template_content

def replace_placeholders(template_content, front_matter):
    for key, value in front_matter.items():
        placeholder = f"${key}$"
        if isinstance(value, list):
            value = ', '.join(value)  # Convert list to a comma-separated string
        template_content = template_content.replace(placeholder, str(value))
    
    # Remove any remaining placeholders that were not replaced
    placeholders = ["${title}$", "${date}$", "${tags}$", "${status}$"]
    for placeholder in placeholders:
        template_content = template_content.replace(placeholder, "")

    return template_content

def convert_md_to_html(md_file, output_file, template_file, front_matter):
    try:
        body_html = pypandoc.convert_file(
            source_file=str(md_file),
            to='html5'
        )

        with open(template_file, 'r', encoding='utf-8') as f:
            template_content = f.read()

        extra_properties = get_extra_properties(config)

        # Merge front matter with extra properties
        front_matter.update(extra_properties)

        # Dynamically load and replace sub-templates
        template_content = load_and_replace_sub_templates(template_content)
        
        # Replace placeholders with front matter values
        template_content = replace_placeholders(template_content, front_matter)
        
        # Insert the body content
        template_content = template_content.replace("$body$", body_html)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        print(f"Converted '{md_file}' to '{output_file}' using template '{template_file}'.")
    except Exception as e:
        print(f"Error converting '{md_file}': {e}")

def main():
    
    # Remove any files not in this build.
    # shutil.rmtree(output_dir)

    # Copy the static folder to the output directory before generating HTML files
    copy_static_folder()

    blog_posts = []

    # Walk through the content directory and its subdirectories
    for root, dirs, files in os.walk(content_dir):
        for filename in files:
            if filename.endswith(".md"):
                input_file = os.path.join(root, filename)
                file_base_name = os.path.splitext(filename)[0]
                relative_path = os.path.relpath(root, content_dir)
                output_subdir = os.path.join(output_dir, relative_path)
                                
                # Check for a template with the same name as the Markdown file (e.g., index.html)
                file_template = os.path.join(template_dir, f"{file_base_name}.html")
                
                if os.path.exists(file_template):
                    template_file = file_template #use a template with the same name.
                else:
                    # Fallback to directory-specific template (e.g., blog.html) or default template
                    directory_template = os.path.join(template_dir, f"{os.path.basename(relative_path)}.html")
                    if os.path.exists(directory_template):
                        template_file = directory_template
                    else:
                        template_file = default_template
                
                front_matter = extract_front_matter(input_file)
                
                # Only generate HTML if the status is published
                if front_matter.get("status") == "published":

                    os.makedirs(output_subdir, exist_ok=True)  # Ensure the output directory exists
                    
                    output_file = os.path.join(output_subdir, f"{file_base_name}.html")

                    convert_md_to_html(input_file, output_file, template_file, front_matter)

                    # If this is the "Blog" directory, collect the blog post data
                    if "blog" in os.path.normpath(root).lower().split(os.sep) and filename.lower() != "index.md":
                        blog_posts.append({
                            "@type": "BlogPosting",
                            "headline": front_matter.get("title", file_base_name.replace("-", " ").title()),
                            "url": f"{file_base_name}.html",
                            "datePublished": front_matter.get("date", "2024-08-25"),  # Example static date, adjust accordingly
                            "keywords": ", ".join(front_matter.get("tags", []))
                            # Add more properties like 'author' or 'description' if available
                        })
    
    # After processing all files, generate the JSON-LD if we processed any blog posts
    if blog_posts:
        generate_blog_json_ld(blog_posts)

def generate_blog_json_ld(blog_posts):
    """Generate a JSON-LD file for the Blog directory in the output directory."""
    blog_output_directory = os.path.join(output_dir, "blog")
    json_file_path = os.path.join(blog_output_directory, "schema.json")
    
    # Ensure the Blog directory exists in the output directory
    if not os.path.exists(blog_output_directory):
        os.makedirs(blog_output_directory)

    # Convert any date objects to ISO format strings
    for post in blog_posts:
        if isinstance(post.get("datePublished"), date):
            post["datePublished"] = post["datePublished"].isoformat()

    # Create the JSON-LD structure
    json_data = {
        "@context": "https://schema.org",
        "@type": "Blog",
        "blogPost": blog_posts
    }
    
    # Write the JSON-LD to the schema.json file in the output directory
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(json_data, json_file, indent=2)
    
    print(f"Generated JSON-LD file: {json_file_path}")

if __name__ == '__main__':
    main()

