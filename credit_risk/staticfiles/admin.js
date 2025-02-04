const apiUrl = '/risk_model/api/predictions/';
let editMode = false; // Track whether we're editing or adding
let currentPredictionId = null; // Store the ID of the prediction being edited
const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;


// Fetch and render predictions
const renderPredictions = async () => {
    try {
        const response = await fetch(apiUrl, { method: 'GET' });
        const predictions = await response.json();

        const tableBody = document.querySelector('#companyTable tbody');
        tableBody.innerHTML = ''; // Clear existing rows

        predictions.forEach(prediction => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${prediction.name}</td>
                <td>${prediction.revenue}</td>
                <td>${prediction.risk_category}</td>
                <td>
                    <button class="edit-btn" data-id="${prediction.id}">Edit</button>
                    <button class="delete-btn" data-id="${prediction.id}">Delete</button>
                </td>
            `;
            tableBody.appendChild(row);
        });

        // Reinitialize DataTables
        $('#companyTable').DataTable();
    } catch (error) {
        console.error('Error fetching predictions:', error);
    }
};

// Edit Prediction
const editPrediction = async (id) => {
    try {
        const response = await fetch(`${apiUrl}${id}/`, { method: 'GET' });
        if (!response.ok) {
            if (response.status === 404) {
                alert('Prediction not found.');
                return;
            }
            throw new Error(`Error fetching prediction: ${response.statusText}`);
        }

        const prediction = await response.json();

        // Populate the form with the prediction data
        document.querySelector('#name').value = prediction.name || ''; // Set "User Input X"
        document.querySelector('#revenue').value = prediction.revenue || 0;
        document.querySelector('#riskCategory').value = prediction.risk_category || '';

        editMode = true; // Enable edit mode
        currentPredictionId = id; // Store ID for editing
    } catch (error) {
        console.error('Error fetching prediction:', error);
    }
};


// Save or Update Prediction
document.querySelector('#companyForm').addEventListener('submit', async (event) => {
    event.preventDefault();

    // const name = document.querySelector('#name').value.trim();
    const revenue = parseFloat(document.querySelector('#revenue').value.trim());
    const riskCategory = document.querySelector('#riskCategory').value;

    if (isNaN(revenue) || typeof revenue!= 'number')  {
        alert('Please provide valid inputs.');
        return;
    }

    const company_name = "Admin";

    const data = {
        cash: 0.0, 
                    total_inventory: 0.0,
                    non_current_asset: 0.0,
                    current_liability: 0.0,
                    gross_profit: 0.0,
                    retained_earnings: 0.0, 
                    earnings_before_interest : 0.0,
                    dividends_per_share : 0.0,
                    total_stockholders_equity: 0.0,
                    total_market_value : 0.0,
                    net_cash_flow: 0.0,
                    total_long_term_debt : 0.0,
                    total_interest_and_related_expense: 0.0,
                    sales_turnover_net : 0.0,
        revenue, risk_category: riskCategory };
    const url = editMode ? `${apiUrl}${currentPredictionId}/` : apiUrl;

    try {
        const response = await fetch(url, {
            method: editMode ? 'PUT' : 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken, // Add CSRF token if required
            },
            body: JSON.stringify(data),
        });

        const result = await response.json();

        if (response.ok && result.status === 'success') {
            alert(editMode ? 'Prediction updated successfully!' : 'Prediction added successfully!');
            const updatedData = result.data;

            if (!editMode) {
                // Append the new prediction to the table
                const tableBody = document.querySelector('#companyTable tbody');
                const newRow = document.createElement('tr');
                const newPrediction = result.data;

                newRow.innerHTML = `
                    <td>${newPrediction.name}</td>
                    <td>${newPrediction.revenue}</td>
                    <td>${newPrediction.risk_category}</td>
                    <td>
                        <button class="edit-btn" data-id="${newPrediction.id}">Edit</button>
                        <button class="delete-btn" data-id="${newPrediction.id}">Delete</button>
                    </td>
                `;
                tableBody.appendChild(newRow);
            } else {
                renderPredictions(); // Refresh the table for updates
            }

            if (editMode) {
                // Update the specific table row
                const row = document.querySelector(`[data-id="${currentPredictionId}"]`).closest('tr');
                row.innerHTML = `
                    <td>${updatedData.name}</td>
                    <td>${updatedData.revenue}</td>
                    <td>${updatedData.risk_category}</td>
                    <td>
                        <button class="edit-btn" data-id="${updatedData.id}">Edit</button>
                        <button class="delete-btn" data-id="${updatedData.id}">Delete</button>
                    </td>
                `;

                // Reattach event listeners to the new buttons
                row.querySelector('.edit-btn').addEventListener('click', () => editPrediction(updatedData.id));
                row.querySelector('.delete-btn').addEventListener('click', () => deletePrediction(updatedData.id));
            } else {
                // Reload the entire table if a new record is added
                renderPredictions();
            }
            document.querySelector('#companyForm').reset(); // Clear form
            editMode = false; // Reset edit mode
            currentPredictionId = null; // Clear current ID
        } else {
            throw new Error(result.message || 'An error occurred');
        }
    } catch (error) {
        console.error('Error saving prediction:', error);
    }
});


// Delete Prediction
const deletePrediction = async (id) => {
    if (confirm('Are you sure you want to delete this prediction?')) {
        try {
            const response = await fetch(`${apiUrl}${id}/`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
            });

            const result = await response.json();
            if (result.status === 'success') {
                alert('Prediction deleted successfully!');
                const rowToDelete = document.querySelector(`button[data-id="${id}"]`).closest('tr');
                if (rowToDelete) {
                    rowToDelete.remove(); // Remove the row from the DOM
                }
            } else {
                alert('Error: ' + result.message);
            }
        } catch (error) {
            console.error('Error deleting prediction:', error);
        }
    }
};

// Attach Event Handlers Dynamically
document.querySelector('#companyTable').addEventListener('click', (event) => {
    const target = event.target;

    if (target.classList.contains('edit-btn')) {
        const id = target.dataset.id;
        editPrediction(id);
    } else if (target.classList.contains('delete-btn')) {
        const id = target.dataset.id;
        deletePrediction(id);
    }
});

// Initialize the page
$(document).ready(() => {
    renderPredictions();
});
