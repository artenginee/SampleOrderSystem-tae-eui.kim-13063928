from controllers.sample_controller import SampleController
from controllers.order_controller import OrderController
from controllers.production_controller import ProductionController
from views.main_view import MainView

if __name__ == "__main__":
    sample_ctrl = SampleController()
    order_ctrl = OrderController()
    prod_ctrl = ProductionController()
    MainView(sample_ctrl, order_ctrl, prod_ctrl).run()
