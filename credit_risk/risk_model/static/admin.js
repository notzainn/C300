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
           /*  const displayName = prediction.name && prediction.name !== "User Input (ID)"
            ? prediction.name
            : prediction.user_input_name || "Unknown"; */
            const row = document.createElement('tr');
            row.innerHTML = `            
                <td>${prediction.name || 'Unnamed Company'}</td>
                <td>${prediction.user_input_id}</td>
                <td>${prediction.revenue}</td>
                <td>${prediction.risk_category}</td>
                <td>
                    <button class="edit-btn" data-id="${prediction.id}">Edit</button>
                    <button class="delete-btn" data-id="${prediction.id}">Delete</button>
                </td>
            `;
            tableBody.appendChild(row);

        });

        if ($.fn.DataTable.isDataTable('#companyTable')) {
            $('#companyTable').DataTable().destroy();
        }
        $('#companyTable').DataTable({
            "pagingType": "full_numbers",
            "lengthMenu": [10, 25, 50, 75, 100],
            "searching": true,
            "ordering": true,
            "info": true,
            "autoWidth": false
        });
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
        document.querySelector('#name').value = prediction.name; 
        document.querySelector('#revenue').value = prediction.revenue || 0;
        document.querySelector('#riskCategory').value = prediction.risk_category || '';

        editMode = true; // Enable edit mode
        currentPredictionId = id; // Store ID for editing
    } catch (error) {
        console.error('Error fetching prediction:', error);
    }
};


// Save Prediction 
document.querySelector('#companyForm').addEventListener('submit', async (event) => {
    event.preventDefault();

    const name = document.querySelector('#name').value.trim();
    const revenue = parseFloat(document.querySelector('#revenue').value.trim());
    const riskCategory = document.querySelector('#riskCategory').value;

    if (!name || isNaN(revenue)) {
        alert('Please provide valid inputs.');
        return;
    }

    if (!currentPredictionId) {
        alert('No prediction selected for editing.');
        return;
    }

    const data = {
        name,
        revenue,
        risk_category: riskCategory,
    };

    const url = `${apiUrl}${currentPredictionId}/`; // Always use PUT for editing

    try {
        const response = await fetch(url, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken, // Add CSRF token if required
            },
            body: JSON.stringify(data),
        });

        const result = await response.json();

        if (response.ok && result.status === 'success') {
            alert('Prediction updated successfully!');

            // Update the specific table row dynamically
            const row = document.querySelector(`button[data-id="${currentPredictionId}"]`).closest('tr');
            row.innerHTML = `
                <td>${result.data.name || 'Unnamed Company'}</td>
                <td>${result.data.user_input_id || 'N/A'}</td>
                <td>${result.data.revenue}</td>
                <td>${result.data.risk_category}</td>
                <td>
                    <button class="edit-btn" data-id="${result.data.id}">Edit</button>
                    <button class="delete-btn" data-id="${result.data.id}">Delete</button>
                </td>
            `;

            // Reattach event listeners to the new buttons
            row.querySelector('.edit-btn').addEventListener('click', () => editPrediction(result.data.id));
            row.querySelector('.delete-btn').addEventListener('click', () => deletePrediction(result.data.id));

            // Clear the form and reset editing state
            document.querySelector('#companyForm').reset();
            editMode = false;
            currentPredictionId = null;
        } else {
            throw new Error(result.message || 'An error occurred');
        }
    } catch (error) {
        console.error('Error updating prediction:', error);
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
