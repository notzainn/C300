$(document).ready(function () {
    // Initialize DataTable
    let userTable = $('#userTable').DataTable();

    // Handle Edit Button Click
    $(".edit-btn").on("click", function () {
        let userId = $(this).data("id");
        let username = $(this).data("username");
        let role = $(this).data("role");

        // Populate the form with existing user data
        $("#editUserId").val(userId);
        $("#editUsername").val(username);
        $("#editRole").val(role);

        $("#editUserForm").attr("action", `/risk_model/edit_user/${userId}/`);
    });
        
 // Handle Form Submission with AJAX
 $("#editUserForm").on("submit", function (e) {
    e.preventDefault(); // Prevent default form submission

    let formData = $(this).serialize(); // Serialize form data
    let actionUrl = $(this).attr("action");

    $.ajax({
        type: "POST",
        url: actionUrl,
        data: formData,
        success: function (response) {
            // On success, update the DataTable dynamically
            let userId = $("#editUserId").val();
            let username = $("#editUsername").val();
            let role = $("#editRole").val();

            // Find the row with the corresponding user ID and update it
            let row = userTable.rows().nodes().to$().find(`td:contains('${userId}')`).parent();
            row.find("td:eq(1)").text(username);
            row.find("td:eq(2)").text(role);

            // Clear the form after submission
            $("#editUserForm")[0].reset();

            alert("User updated successfully!");
        },
        error: function (xhr, status, error) {
            alert("Error updating user: " + error);
        },
    });
});
});
