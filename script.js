// ======================================================
// SETUP
// ======================================================

const API_URL = "http://127.0.0.1:8000";


// Manual form
const form = document.getElementById("record-form");

const nameInput =
  document.getElementById("full-name");

const phoneInput =
  document.getElementById("phone-number");

const recordsBody =
  document.getElementById("records-body");

const messageBox =
  document.getElementById("message");


// AI elements
const aiPrompt =
  document.getElementById("ai-prompt");

const aiCreateButton =
  document.getElementById("ai-create-btn");

const aiMessage =
  document.getElementById("ai-message");


let records = [];
let editingId = null;


// ======================================================
// HELPERS
// ======================================================

function isValidPhone(phone) {

  const allowedChars =
    /^[0-9+\-()\s]+$/;

  const digitCount =
    phone.replace(/\D/g, "").length;

  return (
    allowedChars.test(phone) &&
    digitCount >= 7
  );
}


function showMessage(text, type) {

  messageBox.textContent = text;

  messageBox.className =
    "message " + type;
}


function clearMessage() {

  messageBox.textContent = "";

  messageBox.className = "message";
}


function showAIMessage(text, type) {

  aiMessage.textContent = text;

  aiMessage.className =
    "message " + type;
}


function createButton(
  text,
  className,
  onClick
) {

  const button =
    document.createElement("button");

  button.textContent = text;

  button.className =
    "btn " + className;

  button.type = "button";

  button.addEventListener(
    "click",
    onClick
  );

  return button;
}


// ======================================================
// READ RECORDS
// ======================================================

async function loadRecords() {

  try {

    const response =
      await fetch(
        `${API_URL}/records`
      );


    if (!response.ok) {

      throw new Error(
        "Could not load records."
      );
    }


    const data =
      await response.json();


    records = data.map(
      function (record) {

        return {

          id: record.id,

          name:
            record.full_name,

          phone:
            record.phone_number
        };
      }
    );


    renderTable();

  }

  catch (error) {

    console.error(error);

    showMessage(
      "Could not connect to the server.",
      "error"
    );
  }
}


// ======================================================
// DISPLAY TABLE
// ======================================================

function renderTable() {

  recordsBody.innerHTML = "";


  if (records.length === 0) {

    const emptyRow =
      document.createElement("tr");

    const emptyCell =
      document.createElement("td");


    emptyCell.colSpan = 4;

    emptyCell.className =
      "empty-row";

    emptyCell.textContent =
      "No records found. Add your first record above.";


    emptyRow.appendChild(
      emptyCell
    );

    recordsBody.appendChild(
      emptyRow
    );

    return;
  }


  records.forEach(
    function (record) {

      const row =
        document.createElement("tr");


      const idCell =
        document.createElement("td");

      idCell.textContent =
        record.id;


      const nameCell =
        document.createElement("td");

      const phoneCell =
        document.createElement("td");


      const actionsCell =
        document.createElement("td");

      actionsCell.className =
        "actions";


      // Editing mode
      if (record.id === editingId) {

        const editName =
          document.createElement("input");

        editName.type = "text";

        editName.value =
          record.name;


        const editPhone =
          document.createElement("input");

        editPhone.type = "tel";

        editPhone.value =
          record.phone;


        nameCell.appendChild(
          editName
        );

        phoneCell.appendChild(
          editPhone
        );


        actionsCell.appendChild(

          createButton(
            "Save",
            "btn-save",

            function () {

              updateRecord(
                record.id,
                editName.value,
                editPhone.value
              );
            }
          )
        );


        actionsCell.appendChild(

          createButton(
            "Cancel",
            "btn-cancel",

            function () {

              editingId = null;

              clearMessage();

              renderTable();
            }
          )
        );
      }


      // Normal mode
      else {

        nameCell.textContent =
          record.name;

        phoneCell.textContent =
          record.phone;


        actionsCell.appendChild(

          createButton(
            "Edit",
            "btn-edit",

            function () {

              editingId =
                record.id;

              clearMessage();

              renderTable();
            }
          )
        );


        actionsCell.appendChild(

          createButton(
            "Delete",
            "btn-delete",

            function () {

              deleteRecord(
                record.id
              );
            }
          )
        );
      }


      row.appendChild(
        idCell
      );

      row.appendChild(
        nameCell
      );

      row.appendChild(
        phoneCell
      );

      row.appendChild(
        actionsCell
      );


      recordsBody.appendChild(
        row
      );
    }
  );
}


// ======================================================
// MANUAL CREATE
// ======================================================

async function addRecord(
  name,
  phone
) {

  try {

    const response =
      await fetch(
        `${API_URL}/records`,
        {

          method: "POST",

          headers: {

            "Content-Type":
              "application/json"
          },

          body:
            JSON.stringify({

              full_name: name,

              phone_number:
                phone
            })
        }
      );


    if (!response.ok) {

      throw new Error(
        "Could not create record."
      );
    }


    await loadRecords();


    form.reset();

    nameInput.focus();


    showMessage(
      "Record added successfully.",
      "success"
    );

  }

  catch (error) {

    console.error(error);

    showMessage(
      "Failed to add record.",
      "error"
    );
  }
}


// ======================================================
// AI CREATE
// ======================================================

// ======================================================
// AI CRUD
// ======================================================

async function executeAICommand() {

  const prompt = aiPrompt.value.trim();

  if (prompt === "") {
    showAIMessage(
      "Please enter a command first.",
      "error"
    );
    return;
  }

  try {

    aiCreateButton.disabled = true;
    aiCreateButton.textContent = "Processing...";

    showAIMessage(
      "AI is processing your request...",
      ""
    );

    const response = await fetch(
      `${API_URL}/ai-command`,
      {
        method: "POST",

        headers: {
          "Content-Type": "application/json"
        },

        body: JSON.stringify({
          prompt: prompt
        })
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail ||
        "AI could not perform the operation."
      );
    }

    // Refresh table after CREATE, UPDATE or DELETE
    // Also keeps table synchronized after READ
    await loadRecords();

    // Show AI result
    if (data.operation === "READ") {

      if (data.records.length === 0) {

        showAIMessage(
          "No matching records found.",
          "error"
        );

      } else {

        const resultText = data.records
          .map(function (record) {
            return (
              "ID: " + record.id +
              " | Name: " + record.full_name +
              " | Phone: " + record.phone_number
            );
          })
          .join("   •   ");

        showAIMessage(
          data.message + " " + resultText,
          "success"
        );
      }

    } else {

      showAIMessage(
        data.message,
        "success"
      );
    }

    // Clear textbox
    aiPrompt.value = "";

  } catch (error) {

    console.error(error);

    showAIMessage(
      error.message,
      "error"
    );

  } finally {

    aiCreateButton.disabled = false;

    aiCreateButton.textContent =
      "Run AI Command";
  }
}


// AI button
aiCreateButton.addEventListener(
  "click",
  executeAICommand
);


// ======================================================
// UPDATE
// ======================================================

async function updateRecord(
  id,
  newName,
  newPhone
) {

  newName =
    newName.trim();

  newPhone =
    newPhone.trim();


  if (
    newName === "" ||
    newPhone === ""
  ) {

    showMessage(
      "Full Name and Phone Number cannot be empty.",
      "error"
    );

    return;
  }


  if (!isValidPhone(newPhone)) {

    showMessage(
      "Please enter a valid phone number (at least 7 digits).",
      "error"
    );

    return;
  }


  try {

    const response =
      await fetch(
        `${API_URL}/records/${id}`,
        {

          method: "PUT",

          headers: {

            "Content-Type":
              "application/json"
          },

          body:
            JSON.stringify({

              full_name:
                newName,

              phone_number:
                newPhone
            })
        }
      );


    if (!response.ok) {

      throw new Error(
        "Could not update record."
      );
    }


    editingId = null;


    await loadRecords();


    showMessage(
      "Record updated successfully.",
      "success"
    );

  }

  catch (error) {

    console.error(error);

    showMessage(
      "Failed to update record.",
      "error"
    );
  }
}


// ======================================================
// DELETE
// ======================================================

async function deleteRecord(id) {

  const confirmed =
    confirm(
      "Are you sure you want to delete this record?"
    );


  if (!confirmed) {

    return;
  }


  try {

    const response =
      await fetch(
        `${API_URL}/records/${id}`,
        {
          method: "DELETE"
        }
      );


    if (!response.ok) {

      throw new Error(
        "Could not delete record."
      );
    }


    if (editingId === id) {

      editingId = null;
    }


    await loadRecords();


    showMessage(
      "Record deleted.",
      "success"
    );

  }

  catch (error) {

    console.error(error);

    showMessage(
      "Failed to delete record.",
      "error"
    );
  }
}


// ======================================================
// MANUAL FORM SUBMIT
// ======================================================

form.addEventListener(
  "submit",

  function (event) {

    event.preventDefault();


    const name =
      nameInput.value.trim();

    const phone =
      phoneInput.value.trim();


    if (
      name === "" ||
      phone === ""
    ) {

      showMessage(
        "Please fill in both Full Name and Phone Number.",
        "error"
      );

      return;
    }


    if (!isValidPhone(phone)) {

      showMessage(
        "Please enter a valid phone number (at least 7 digits).",
        "error"
      );

      return;
    }


    addRecord(
      name,
      phone
    );
  }
);


// ======================================================
// INITIAL LOAD
// ======================================================

loadRecords();