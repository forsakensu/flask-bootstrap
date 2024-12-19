const showAlert = (message, type, alertPlaceholder) => {
  const wrapper = document.createElement("div");
  wrapper.innerHTML = [
    `<div class="alert alert-${type} alert-dismissible" role="alert">`,
    `   <div>${message}</div>`,
    '   <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>',
    "</div>",
  ].join("");
  alertPlaceholder.insertAdjacentElement("afterbegin", wrapper);
  setTimeout(() => {
    wrapper.remove();
  }, 5000);
};

const formEl = document.querySelector("form");

const myHeaders = new Headers();
myHeaders.append("Content-Type", "application/json");

const makeRequest = async () => {
  const form_data = JSON.stringify(Object.fromEntries(new FormData(formEl)));
  console.log(form_data);
  try {
    const response = await fetch(formEl.action, {
      method: "post",
      headers: myHeaders,
      body: form_data,
    });
    if (!response.ok) {
      throw new Error(response.statusText);
    }
    const data = await response.json();
    formEl.reset();
    showAlert(data.message, "success", formEl);
  } catch (error) {
    showAlert(`Произошла ошибка: ${error}`, "danger", formEl);
  }
};

formEl.addEventListener("submit", (evt) => {
  evt.preventDefault();
  makeRequest();
});
