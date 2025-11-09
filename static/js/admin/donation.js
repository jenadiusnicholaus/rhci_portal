(function($) {
    $(document).ready(function() {
        // Highlight status changes
        $('.field-status select').on('change', function() {
            $(this).addClass('changed');
        });

        // Format currency amounts
        $('.field-amount input').on('blur', function() {
            let value = $(this).val();
            if (value) {
                $(this).val(parseFloat(value).toFixed(2));
            }
        });
    });
})(django.jQuery);