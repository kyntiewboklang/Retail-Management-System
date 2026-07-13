

const searchInput = document.getElementById("searchProduct");
const searchBtn = document.getElementById("searchBtn");
const categoryFilter = document.getElementById("categoryFilter");

function searchProducts() {

    const searchText = searchInput.value.toLowerCase();
    const selectedCategory = categoryFilter.value.toLowerCase();

    const rows = document.querySelectorAll("#stockTable tbody tr");

    rows.forEach(row => {

        const sku = row.cells[0].innerText.toLowerCase();
        const product = row.cells[1].innerText.toLowerCase();
        const category = row.cells[2].innerText.toLowerCase();
        const brand = row.cells[3].innerText.toLowerCase();

        const matchesSearch =
            sku.includes(searchText) ||
            product.includes(searchText) ||
            category.includes(searchText) ||
            brand.includes(searchText);

        const matchesCategory =
            selectedCategory === "" ||
            category === selectedCategory;

        if (matchesSearch && matchesCategory) {
            row.style.display = "";
        } else {
            row.style.display = "none";
        }

    });

}

searchBtn.addEventListener("click", searchProducts);

searchInput.addEventListener("keyup", searchProducts);
categoryFilter.addEventListener("change", searchProducts);
