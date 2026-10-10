from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response

from app.companies.service import CompaniesService
from app.deps import CurrentUser, Session, respond, responses
from app.errors import ConflictError, NotFoundError
from app.schemas import (
    CreateCompanyRequestContent,
    CreateCompanyResponseContent,
    GetCompanyResponseContent,
    ListCompaniesResponseContent,
    UpdateCompanyRequestContent,
    UpdateCompanyResponseContent,
)

router = APIRouter(tags=["Companies"])
CompanyId = Annotated[str, Path(min_length=1, max_length=64)]


def companies_service(session: Session) -> CompaniesService:
    return CompaniesService(session)


Companies = Annotated[CompaniesService, Depends(companies_service)]


@router.get(
    "/api/companies",
    operation_id="ListCompanies",
    response_model=ListCompaniesResponseContent,
    response_model_exclude_none=True,
    responses=responses(),
)
async def list_companies(user: CurrentUser, companies: Companies) -> Response:
    return respond(ListCompaniesResponseContent(items=await companies.list(user.id)))


@router.post(
    "/api/companies",
    operation_id="CreateCompany",
    status_code=201,
    response_model=CreateCompanyResponseContent,
    response_model_exclude_none=True,
    responses=responses(ConflictError),
)
async def create_company(
    body: CreateCompanyRequestContent, user: CurrentUser, companies: Companies
) -> Response:
    company = await companies.create(
        name=body.name, description=body.description, created_by=user.id
    )
    return respond(CreateCompanyResponseContent(company=company), 201)


@router.get(
    "/api/companies/{companyId}",
    operation_id="GetCompany",
    response_model=GetCompanyResponseContent,
    response_model_exclude_none=True,
    responses=responses(NotFoundError),
)
async def get_company(companyId: CompanyId, user: CurrentUser, companies: Companies) -> Response:
    return respond(GetCompanyResponseContent(company=await companies.get(companyId, user.id)))


@router.patch(
    "/api/companies/{companyId}",
    operation_id="UpdateCompany",
    response_model=UpdateCompanyResponseContent,
    response_model_exclude_none=True,
    responses=responses(NotFoundError, ConflictError),
)
async def update_company(
    companyId: CompanyId,
    body: UpdateCompanyRequestContent,
    user: CurrentUser,
    companies: Companies,
) -> Response:
    company = await companies.update(
        companyId, name=body.name, description=body.description, user_id=user.id
    )
    return respond(UpdateCompanyResponseContent(company=company))
