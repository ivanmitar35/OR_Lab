document.addEventListener("DOMContentLoaded", () => {
  const table = new DataTable("#zdenciTable", {
    ajax: {
      url: "/api/zdenci",
      dataSrc: "data",
    },
    serverSide: true,
    processing: true,
    columns: [
      { data: "lokacija", title: "Lokacija" },
      { data: "naziv_gc", title: "Gradska četvrt" },
      { data: "tip_zdenca", title: "Tip zdenca" },
      { data: "status_odrz", title: "Status održavanja" },
      { data: "aktivan_da_ne", title: "Aktivan" },
      { data: "teren_dane", title: "Stanje terena" },
      { data: "vlasnik_ki", title: "Vlasnik" },
      { data: "odrzava_ki", title: "Održava" },
      { data: "zkc_oznaka", title: "ZK čestica" },
      { data: "broj_vodomjera", title: "Broj vodomjera" },
      { data: "napomena_teren", title: "Napomena teren" },
      { data: "pozicija_tocnost", title: "Točnost pozicije" },
      { data: "lon", title: "Lon" },
      { data: "lat", title: "Lat" },
    ],
    pageLength: 50,
    fixedHeader: true,
    columnControl: [
      {
        target: 0,
        content: ["order"],
      },
      {
        target: 1,
        content: ["search"],
      },
    ],
    scrollX: true,
    language: {
      lengthMenu: "Prikaži _MENU_ zapisa po stranici",
      search: "Pretraži:",
      info: "Prikazujem _START_ do _END_ od ukupno _TOTAL_ zapisa",
      infoEmpty: "Nema dostupnih zapisa",
      infoFiltered: "(filtrirano iz ukupno _MAX_ zapisa)",
      loadingRecords: "Učitavanje...",
      zeroRecords: "Nema pronađenih zapisa",
      emptyTable: "Nema podataka u tablici",
    },
  });
  //////////
  function downloadFile(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }
  ///////////

  async function downloadExport(format, filename) {
    const params = new URLSearchParams();
    const dtParams = table.ajax && table.ajax.params ? table.ajax.params() : null;

    if (dtParams && dtParams.search && dtParams.search.value) {
      params.set("search", dtParams.search.value);
    } else {
      const searchValue = table.search();
      if (searchValue) params.set("search", searchValue);
    }

    if (dtParams && Array.isArray(dtParams.columns)) {
      dtParams.columns.forEach((column, index) => {
        if (column.search && column.search.value) {
          params.set(`columns[${index}][search][value]`, column.search.value);
        }
        if (column.columnControl && column.columnControl.search) {
          const cc = column.columnControl.search;
          if (cc.value) {
            params.set(`columns[${index}][columnControl][search][value]`, cc.value);
          }
          if (cc.logic) {
            params.set(`columns[${index}][columnControl][search][logic]`, cc.logic);
          }
          if (cc.type) {
            params.set(`columns[${index}][columnControl][search][type]`, cc.type);
          }
        }
      });
    } else {
      const columnCount = table.columns().count();
      for (let i = 0; i < columnCount; i += 1) {
        const columnValue = table.column(i).search();
        if (columnValue) {
          params.set(`columns[${i}][search][value]`, columnValue);
        }
      }
    }

    const query = params.toString();
    const url = query
      ? `/api/zdenci/export?format=${format}&${query}`
      : `/api/zdenci/export?format=${format}`;

    const response = await fetch(url);
    if (!response.ok) {
      console.error(`Export failed: ${response.status}`);
      return;
    }

    const blob = await response.blob();
    downloadFile(blob, filename);
  }

  document.getElementById("downloadCsv").addEventListener("click", () => {
    downloadExport("csv", "zdenci_filtered.csv");
  });

  document.getElementById("downloadJson").addEventListener("click", () => {
    downloadExport("json", "zdenci_filtered.json");
  });

});
