document.addEventListener("DOMContentLoaded", () => {
  const table = new DataTable("#zdenciTable", {
    ajax: {
      url: "/api/zdenci",
      dataSrc: "",
    },
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
  function downloadBlob(content, filename, mime) {
    const blob = new Blob([content], { type: mime });
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

  const exportColumns = [
    { key: "naziv_gc", title: "naziv_gc" },
    { key: "lokacija", title: "lokacija" },
    { key: "tip_zdenca", title: "tip_zdenca" },
    { key: "status_odrz", title: "status_odrz" },
    { key: "aktivan_da_ne", title: "aktivan_da_ne" },
    { key: "teren_dane", title: "teren_dane" },
    { key: "vlasnik_ki", title: "vlasnik_ki" },
    { key: "odrzava_ki", title: "odrzava_ki" },
    { key: "zkc_oznaka", title: "zkc_oznaka" },
    { key: "broj_vodomjera", title: "broj_vodomjera" },
    { key: "napomena_teren", title: "napomena_teren" },
    { key: "pozicija_tocnost", title: "pozicija_tocnost" },
    { key: "lon", title: "lon" },
    { key: "lat", title: "lat" },
  ];



  document.getElementById("downloadCsv").addEventListener("click", () => {
    const rows = table.rows({ search: "applied" }).data().toArray();

    rows.sort((a, b) => {
      const g1 = (a.naziv_gc || "").localeCompare(b.naziv_gc || "");
      if (g1 !== 0) return g1;
      return (a.lokacija || "").localeCompare(b.lokacija || "");
    });

    const exportColumns = [
      { key: "naziv_gc", title: "naziv_gc" },
      { key: "lokacija", title: "lokacija" },
      { key: "tip_zdenca", title: "tip_zdenca" },
      { key: "status_odrz", title: "status_odrz" },
      { key: "aktivan_da_ne", title: "aktivan_da_ne" },
      { key: "teren_dane", title: "teren_dane" },
      { key: "vlasnik_ki", title: "vlasnik_ki" },
      { key: "odrzava_ki", title: "odrzava_ki" },
      { key: "zkc_oznaka", title: "zkc_oznaka" },
      { key: "broj_vodomjera", title: "broj_vodomjera" },
      { key: "napomena_teren", title: "napomena_teren" },
      { key: "pozicija_tocnost", title: "pozicija_tocnost" },
      { key: "lon", title: "lon" },
      { key: "lat", title: "lat" }
    ];

    let csv = exportColumns.map(c => c.title).join(",") + "\n";

    rows.forEach(row => {
      const line = exportColumns.map(c => {
        let v = row[c.key];
        if (v === null || v === undefined) v = "";
        v = String(v).trim();

        if (/^-?\d+(\.\d+)?$/.test(v)) return v;
        if (v.includes('"') || v.includes(',') || v.includes(';')) {
          v = v.replace(/"/g, '""');
          return `"${v}"`;
        }
        if (v.includes(' ')) return `"${v}"`;
        return v;
      }).join(",");
      csv += line + "\n";
    });

    downloadBlob(csv, "zdenci_filtered.csv", "text/csv;charset=utf-8;");
  });



  document.getElementById("downloadJson").addEventListener("click", () => {
    const rows = table.rows({ search: "applied" }).data().toArray();

    rows.sort((a, b) => {
      const g1 = (a.naziv_gc || "").localeCompare(b.naziv_gc || "");
      if (g1 !== 0) return g1;
      return (a.lokacija || "").localeCompare(b.lokacija || "");
    });

    const exportColumns = [
      "lokacija",
      "tip_zdenca",
      "status_odrz",
      "aktivan_da_ne",
      "teren_dane",
      "vlasnik_ki",
      "odrzava_ki",
      "zkc_oznaka",
      "broj_vodomjera",
      "napomena_teren",
      "pozicija_tocnost",
      "lon",
      "lat"
    ];

    const grouped = {};
    rows.forEach(row => {
      const gc = row.naziv_gc || "Nepoznato";
      if (!grouped[gc]) grouped[gc] = [];
      const z = {};
      exportColumns.forEach(k => {
        let v = row[k];
        if (v === "") v = null;
        if ((k === "lon" || k === "lat") && v !== null) {
          const num = Number(v);
          v = Number.isFinite(num) ? num : null;
        }
        z[k] = v;
      });
      grouped[gc].push(z);
    });

    const result = Object.keys(grouped).map(gc => ({
      naziv_gc: gc,
      zdenci: grouped[gc]
    }));

    const json = JSON.stringify(result, null, 2);
    downloadBlob(json, "zdenci_filtered.json", "application/json;charset=utf-8;");
  });

});