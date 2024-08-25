// Function to load and generate list items from schema.json
function loadListItems() {
    fetch('schema.json')
        .then(response => {
            if (!response.ok) {
                // If the schema.json file doesn't exist, skip adding the list
                if (response.status === 404) {
                    console.log('schema.json not found, skipping list generation.');
                    return null;
                }
                throw new Error('Error loading schema.json');
            }
            return response.json();
        })
        .then(data => {
            if (data) {
                // Generate the list of items from the JSON data
                const listItemsContainer = document.getElementById('list-items');
                const ul = document.createElement('ul');

                data.blogPost.forEach(post => {
                    const li = document.createElement('li');
                    const a = document.createElement('a');
                    a.href = post.url;
                    a.textContent = post.headline;
                    li.appendChild(a);
                    ul.appendChild(li);
                });

                // Append the list to the container
                listItemsContainer.appendChild(ul);
            }
        })
        .catch(error => console.error('Error loading list items:', error));
}

// Call the function to load and display list items
loadListItems();
