//����java�ļ��е�����Ե��룬���Ƕ������Ǹ�jave�ļ��е�������ķ����޷���������
package demo.demo2;
import demo.demo.Animal;
import demo.demo.Anmial_generate;
import demo.demo.Cat;
import demo.demo.Dog;
import demo.demo.Live_cat;
import demo.demo.Live_dog;
//import demo.demo.show;

public class demo2 {
	public static void main(String args[]) {

		class People<T> {// ��Ϊ����������֮�ڶ���ģ����Բ�����Ҫstatic�ؼ��ʣ��Ա��������пɵ���
			// ������һ��������
			int age;
			String name;
			private T t;// ����һ������

			public People(int age, String name) { // ���췽��
				this.age = age;
				this.name = name;
			}

			public void add(T t) {
				this.t = t;
			}

			public T get() {
				return this.t;
			}

			public void hunting(Animal animal) { // ���е���ͨ���������
				System.out.println("a human named " + this.name + " is hunting a " + animal.name);
			}

			public <E> void fun(E[] array) { // ����һ�����ͷ���
				for (E element : array) {
					System.out.println(element);
				}
			}

		}

		// main �е�first��Ҫִ������
		Dog snoopy = new Dog(3, "yellow", "female", "dog");
		Cat amy = new Cat(2, "white", "female", "cat");
		snoopy.move();
		amy.eat("fish");
		amy.live(new Live_cat());
		snoopy.live(new Live_dog());

		System.out.println("now human is doing something bad...");
		People people = new People<String>(33, "Tom");
		people.add("this man is a bad guy!");
		System.out.println(people.get());

		String[] s = { "black man ", "white man ", "yellow man " };
		people.fun(s);

		people.hunting(new Animal(4, "white", "female", "jack"));
		//animal_protected();// ���ö��������������ⲿ�ķ���

		// main�е�second��Ҫִ������
		Animal animal = new Dog(10, "red", "female", "dog_red"); // ����ת��
		animal.live(new Live_dog()); // ����dog���������live����

		Dog d = (Dog) animal; // ����ת��
		d.move(); // ����dog��move����
		//show(d);// �������������ⲿ�������жϺ���

	}


	
}
