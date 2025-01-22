const apiUrl = '/risk_model/companies/';

// Function to fetch and render the company table
const renderTable = async () => {
    try {
        const response = await fetch(apiUrl, { method: 'GET' });
        const companies = await response.json();

        const tableBody = document.querySelector('#companyTable tbody');
        tableBody.innerHTML = ''; // Clear existing rows

        companies.forEach(company => {
            const row = document.createElement('tr');

            row.innerHTML = `
                <td>${company.name}</td>
                <td>${company.revenue}</td>
                <td>${company.risk_category}</td>
                <td>
                    <button onclick="editCompany(${company.id})">Edit</button>
                    <button onclick="deleteCompany(${company.id})">Delete</button>
                </td>
            `;

            tableBody.appendChild(row);
        });
    } catch (error) {
        console.error('Error fetching companies:', error);
        alert('Failed to load company data.');
    }
};

// Function to handle form submission for Create/Update
document.getElementById('companyForm').addEventListener('submit', async event => {
    event.preventDefault();

    const name = document.getElementById('name').value.trim();
    const revenue = parseFloat(document.getElementById('revenue').value.trim());
    const riskCategory = document.getElementById('riskCategory').value;

    if (!name || isNaN(revenue) || revenue <= 0) {
        alert('Please provide valid inputs for the form.');
        return;
    }

    const data = { name, revenue, riskCategory };

    try {
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });

        const result = await response.json();

        if (result.status === 'success') {
            alert(result.created ? 'Company added successfully!' : 'Company updated successfully!');
            renderTable();
            event.target.reset(); // Clear the form
        } else {
            alert('An error occurred: ' + result.message);
        }
    } catch (error) {
        console.error('Error saving company:', error);
        alert('Failed to save company data.');
    }
});

// Edit a company
const editCompany = async id => {
    try {
        const response = await fetch(apiUrl, { method: 'GET' });
        const companies = await response.json();
        const company = companies.find(c => c.id === id);

        if (company) {
            document.getElementById('name').value = company.name;
            document.getElementById('revenue').value = company.revenue;
            document.getElementById('riskCategory').value = company.risk_category;
        } else {
            alert('Company not found.');
        }
    } catch (error) {
        console.error('Error editing company:', error);
        alert('Failed to load company data for editing.');
    }
};

// Delete a company
const deleteCompany = async id => {
    if (confirm('Are you sure you want to delete this company?')) {
        try {
            const response = await fetch(apiUrl, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id }),
            });

            const result = await response.json();

            if (result.status === 'success') {
                alert('Company deleted successfully!');
                renderTable();
            } else {
                alert('An error occurred: ' + result.message);
            }
        } catch (error) {
            console.error('Error deleting company:', error);
            alert('Failed to delete company.');
        }
    }
};

// Initial rendering of the table
renderTable();
