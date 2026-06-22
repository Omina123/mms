import pandas as pd
import psycopg2

conn = psycopg2.connect("postgresql://omina_user:JgBK2eNuLzR51Q2jYccrERANImp2azc6@dpg-d85eptbrjlhs73dufp0g-a.ohio-postgres.render.com/omina")

df = pd.read_sql("SELECT * FROM your_table", conn)

df.to_csv("output.csv", index=False)