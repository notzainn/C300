// Fetch stored companies from localStorage or initialize an empty array
let companies = JSON.parse(localStorage.getItem('companies')) || [];

// Function to render the company table
const renderTable = () => {
    const tableBody = document.querySelector('#companyTable tbody');
    tableBody.innerHTML = ''; // Clear existing rows

    companies.forEach((company, index) => {
        const row = document.createElement('tr');

        row.innerHTML = `
            <td>${company.name}</td>
            <td>${company.revenue}</td>
            <td>${company.riskCategory}</td>
            <td>
                <button onclick="editCompany(${index})">Edit</button>
                <button onclick="deleteCompany(${index})">Delete</button>
            </td>
        `;

        tableBody.appendChild(row);
    });
};

// Function to save companies to localStorage
const saveCompanies = () => {
    localStorage.setItem('companies', JSON.stringify(companies));
};

// Handle form submission for Create/Update
document.getElementById('companyForm').addEventListener('submit', event => {
    event.preventDefault();

    const name = document.getElementById('name').value.trim();
    const revenue = parseFloat(document.getElementById('revenue').value.trim());
    const riskCategory = document.getElementById('riskCategory').value;

    const existingIndex = companies.findIndex(company => company.name === name);

    if (existingIndex > -1) {
        // Update existing company
        companies[existingIndex] = { name, revenue, riskCategory };
        alert('Company updated successfully!');
    } else {
        // Create new company
        companies.push({ name, revenue, riskCategory });
        alert('Company added successfully!');
    }

    saveCompanies();
    renderTable();
    event.target.reset(); // Clear the form
});

// Edit a company
const editCompany = index => {
    const company = companies[index];
    document.getElementById('name').value = company.name;
    document.getElementById('revenue').value = company.revenue;
    document.getElementById('riskCategory').value = company.riskCategory;
};

// Delete a company
const deleteCompany = index => {
    if (confirm('Are you sure you want to delete this company?')) {
        companies.splice(index, 1);
        saveCompanies();
        renderTable();
    }
};

// Initial rendering of the table
renderTable();