from typing import List

from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass

class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    student_number: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)

    grades: Mapped[List["Grade"]] = relationship("Grade", back_populates="student")

class Grade(Base):
    __tablename__ = "grades"

    id: Mapped[int] = mapped_column(primary_key=True)
    value: Mapped[int] = mapped_column(Integer, nullable=False)
    subject: Mapped[str] = mapped_column(String(50), nullable=False)
    student_id: Mapped[int] = mapped_column(Integer,ForeignKey("students.id"), nullable=False)

    student = relationship("Student", back_populates="grades")