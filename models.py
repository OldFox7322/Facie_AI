from pydantic import BaseModel, Field, ConfigDict


class FriendCreate(BaseModel):
	name: str = Field(..., alias = 'Name')
	profession: str = Field(..., alias = 'Profession')
	profession_description: str = Field(..., alias = 'ProfessionDescription')
	model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )


class FriendResponse(FriendCreate):
	friend_id: str = Field(..., alias = 'FriendID') 
	S3Key: str 
	PhotoUrl: str 
	model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )


class Questions(BaseModel):
	question: str