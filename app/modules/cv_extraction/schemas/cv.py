from app.core.base_model import RequestSchema


class ProcessCVRequest(RequestSchema):
	cv_file_url: str
