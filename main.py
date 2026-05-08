from database.db_manager import DatabaseManager
from repositories.sample_repository import SampleRepository
from repositories.order_repository import OrderRepository
from repositories.production_job_repository import ProductionJobRepository
from controllers.sample_controller import SampleController
from controllers.order_controller import OrderController
from controllers.production_controller import ProductionController
from views.main_view import MainView

if __name__ == "__main__":
    db          = DatabaseManager.get_instance()
    sample_repo = SampleRepository(db)
    order_repo  = OrderRepository(db)
    job_repo    = ProductionJobRepository(db)

    sample_ctrl = SampleController(sample_repo)
    order_ctrl  = OrderController(order_repo)
    prod_ctrl   = ProductionController(job_repo)

    MainView(sample_ctrl, order_ctrl, prod_ctrl).run()
