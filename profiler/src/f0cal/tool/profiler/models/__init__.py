from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime

Base = declarative_base()


class Device(Base):
    __tablename__ = "device"
    id = Column(Integer, primary_key=True)
    gpu = Column(String)
    cpu = Column(String)
    clock_speed = Column(Integer)

    trace_runs = relationship("TraceRun", back_populates="device")


class TraceRun(Base):
    __tablename__ = "trace_run"
    id = Column(Integer, primary_key=True)
    session_hash = Column(String)
    ran_at = Column(DateTime, default=datetime.now)
    executable_name = Column(String)
    args = Column(String)

    device_id = Column(Integer, ForeignKey("device.id"))
    device = relationship("Device", back_populates="trace_runs")


class TraceEvent(Base):
    __tablename__ = "trace_event"
    id = Column(Integer, primary_key=True)
    thead_clock_delta = Column(Integer)
    time_delta = Column(Float)
    cpu_id = Column(Integer)
    pthread_id = Column(Integer)
    event_type = Column(String)

    trace_id = Column(Integer, ForeignKey("trace_event.id"))
    callable_id = Column(Integer)
    _callable = Column(Integer, ForeignKey("code_callable.id"))


class CodeCallable(Base):
    __tablename__ = "code_callable"

    id = Column(Integer, primary_key=True)
    demangled_name = Column(String)


class CodeArg(Base):
    __tablename__ = "code_arg"
    id = Column(Integer, primary_key=True)
    code_callable_id = Column(Integer, ForeignKey("code_callable.id"), primary_key=True)
    code_callable = relationship("CodeCallable", back_populates="code_args")

    code_type_id = Column(Integer, ForeignKey("code_type.id"), primary_key=True)
    code_type = relationship("CodeTypes", back_populates="code_args")
    position = Column(Integer)


class CodeTypes(Base):
    __tablename__ = "code_type"
    id = Column(Integer, primary_key=True)
    arg_type = Column(String)


class CodeTypesAttrInstance(Base):
    __tablename__ = "code_type_attr_instance"
    id = Column(Integer, primary_key=True)
    # Todo male this an enum?
    _type = Column(String)

    mapper_args__ = {"polymorphic_identity": __tablename__, "polymorphic_on": _type}
    code_arg_id = Column(Integer, ForeignKey("code_arg.id"))


class SizeAttrInstance(CodeTypesAttrInstance):
    __tablename__ = "size_attr_instance"
    id = Column(Integer, ForeignKey("code_type_attr_instance.id"), primary_key=True)
    y = Column(Integer)
    x = Column(Integer)
    __mapper_args__ = {"polymorphic_identity": __tablename__}


class PointerAttrInstance(CodeTypesAttrInstance):
    __tablename__ = "pointer_attr_instance"
    id = Column(Integer, ForeignKey("code_type_attr_instance.id"), primary_key=True)
    value = Column(String)
    __mapper_args__ = {"polymorphic_identity": __tablename__}


if __name__ == "__main__":
    from sqlalchemy import create_engine

    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
