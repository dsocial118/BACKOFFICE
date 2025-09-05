(function ($) {
  // Inicialización Select2 para el campo de técnicos
  $(function () {
    var $el = $('.js-tecnico');
    if (!$el.length) return;

    if (typeof $.fn.select2 !== 'function') {
      // Select2 no está cargado aún; evita romper la página
      return;
    }

    $el.select2({
      maximumSelectionLength: 2,
      width: '100%',
      placeholder: $el.data('placeholder') || 'Selecciona hasta 2 técnicos',
      language: {
        maximumSelected: function () {
          return 'Puedes seleccionar hasta 2 técnicos';
        },
        noResults: function () { return 'Sin resultados'; },
        searching: function () { return 'Buscando…'; }
      }
    });
  });
})(jQuery);

