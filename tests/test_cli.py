import pytest
from typer.testing import CliRunner
from pathlib import Path
import yaml

from expense_splitter.cli import app
from expense_splitter.storage import load_purchases

runner = CliRunner()

@pytest.fixture
def temp_data_dir(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir

def test_init_command(temp_data_dir):
    result = runner.invoke(app, ["init", "--data-dir", str(temp_data_dir)])
    assert result.exit_code == 0
    assert "Initialized data" in result.stdout
    assert (temp_data_dir / "participants.yaml").exists()
    assert (temp_data_dir / "purchases.yaml").exists()

def test_init_with_examples(temp_data_dir):
    result = runner.invoke(app, ["init", "--data-dir", str(temp_data_dir), "--with-examples"])
    assert result.exit_code == 0
    assert "with examples" in result.stdout
    purchases = load_purchases(temp_data_dir / "purchases.yaml")
    assert len(purchases) == 3

def test_add_purchase(temp_data_dir):
    # Init first
    runner.invoke(app, ["init", "--data-dir", str(temp_data_dir)])
    
    result = runner.invoke(app, [
        "add-purchase", 
        "Coffee", 
        "150.00", 
        "Павел", 
        "--group", "809 кабинет",
        "--data-dir", str(temp_data_dir)
    ])
    assert result.exit_code == 0
    assert "Added purchase: Coffee" in result.stdout
    
    purchases = load_purchases(temp_data_dir / "purchases.yaml")
    assert len(purchases) == 1
    assert purchases[0].title == "Coffee"
    assert purchases[0].amount == 150.00
    assert purchases[0].payer == "Павел"

def test_add_purchase_invalid_payer(temp_data_dir):
    runner.invoke(app, ["init", "--data-dir", str(temp_data_dir)])
    result = runner.invoke(app, [
        "add-purchase", "Coffee", "150.00", "Unknown", "--group", "809 кабинет", "--data-dir", str(temp_data_dir)
    ])
    assert result.exit_code == 1
    assert "Error: Payer 'Unknown' not found" in result.stdout

def test_list_purchases(temp_data_dir):
    runner.invoke(app, ["init", "--data-dir", str(temp_data_dir), "--with-examples"])
    result = runner.invoke(app, ["list-purchases", "--data-dir", str(temp_data_dir)])
    assert result.exit_code == 0
    assert "Кофе в офис" in result.stdout
    assert "Обед" in result.stdout

def test_balances(temp_data_dir):
    runner.invoke(app, ["init", "--data-dir", str(temp_data_dir), "--with-examples"])
    result = runner.invoke(app, ["balances", "--data-dir", str(temp_data_dir)])
    assert result.exit_code == 0
    assert "Net Balance" in result.stdout
    assert "Павел" in result.stdout

def test_settle(temp_data_dir):
    runner.invoke(app, ["init", "--data-dir", str(temp_data_dir), "--with-examples"])
    result = runner.invoke(app, ["settle", "--data-dir", str(temp_data_dir)])
    assert result.exit_code == 0
    assert "Amount" in result.stdout

def test_report(temp_data_dir):
    runner.invoke(app, ["init", "--data-dir", str(temp_data_dir), "--with-examples"])
    report_path = temp_data_dir / "report.md"
    result = runner.invoke(app, ["report", "--output", str(report_path), "--data-dir", str(temp_data_dir)])
    assert result.exit_code == 0
    assert report_path.exists()
    content = report_path.read_text()
    assert "# Expense Splitter Report" in content
    assert "Summary of Balances" in content
