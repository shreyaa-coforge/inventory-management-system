import main


def test_banner_shows_number_of_low_stock_products(connection, capsys):
    main.show_low_stock_banner(connection)
    assert "2 product(s)" in capsys.readouterr().out